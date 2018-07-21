import json
from datetime import timedelta as TimeDelta
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from ..wallupdater import (
    WallUpdater, MIN_PERIOD_FOR_STATS, VkApiParsingError,
    MIN_POSTS_NUM_FOR_STATS, MIN_LIFETIME_OF_POST
)
from communities.models import Community, Post


class WallUpdaterTest(TestCase):

    def test_period_for_statistics_is_over(self):
        now = timezone.now()
        wu = WallUpdater(None)
        wu._period_start = now
        with patch('django.utils.timezone.now', return_value=now + MIN_PERIOD_FOR_STATS):
            self.assertTrue(wu._period_for_statistics_is_over())
        with patch('django.utils.timezone.now', return_value=now + MIN_PERIOD_FOR_STATS - TimeDelta(seconds=1)):
            self.assertFalse(wu._period_for_statistics_is_over())

    def test_parsing_error_does_not_stop_work(self):
        vk_api = Mock()
        vk_api.get_community_wall.return_value = [{'id': None}] * 3
        wu = WallUpdater(vk_api)
        with patch.object(wu, '_current_community') as _current_community,\
                patch.object(wu, '_parse_post') as _parse_post:
            _current_community.return_value = Mock(wall_checked_at=None)
            _parse_post.side_effect = [42, VkApiParsingError(), 42]
            posts = wu._get_new_posts()
        self.assertEquals(posts, [42, 42])

    def test_wall_stats_calculation(self):
        check_time = timezone.now()
        comm = Community.objects.create(vkid=42, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE)
        posts = [
            Post.objects.create(
                community=comm,
                vkid=i,
                checked_at=check_time,
                published_at=check_time - MIN_LIFETIME_OF_POST,
                content=[],
                views=100 + 10 * i,
                likes=10 + i,
                shares=1,
                comments=0,
                marked_as_ads=False,
                links=0,
            )
            for i in range(MIN_POSTS_NUM_FOR_STATS)
        ]
        views_per_post = self._median([p.views for p in posts])
        likes_per_view = self._median([p.likes / p.views for p in posts])
        wu = WallUpdater(None)
        wu._check_time = check_time
        with patch.object(wu, '_current_community') as _current_community:
            _current_community.return_value = comm
            wu._update_wall_stats()
            self.assertAlmostEqual(comm.views_per_post, views_per_post)
            self.assertAlmostEqual(comm.likes_per_view, likes_per_view)

    @staticmethod
    def _median(seq):
        seq = sorted(seq)
        if len(seq) % 2 == 1:
            return seq[len(seq) // 2]
        else:
            half = len(seq) // 2
            return (seq[half - 1] + seq[half]) / 2

    def test_wall_stats_are_reset_when_too_few_posts(self):
        check_time = timezone.now()
        comm = Community.objects.create(vkid=42, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE,
                                        views_per_post=100, likes_per_view=0.1)
        for i in range(MIN_POSTS_NUM_FOR_STATS - 1):
            Post(
                community=comm,
                vkid=i,
                checked_at=check_time,
                published_at=check_time - MIN_LIFETIME_OF_POST,
                content=[],
                views=100,
                likes=10,
                shares=1,
                comments=0,
                marked_as_ads=False,
                links=0,
            ).save()
        wu = WallUpdater(None)
        wu._check_time = check_time
        with patch.object(wu, '_current_community') as _current_community:
            _current_community.return_value = comm
            wu._update_wall_stats()
            self.assertIsNone(comm.views_per_post)
            self.assertIsNone(comm.likes_per_view)

    def test_load_accessible_communities(self):
        communities = [
            Community.objects.create(vkid=1, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE, followers=0),
            Community.objects.create(vkid=2, deactivated=False, ctype=Community.TYPE_OPEN_GROUP, followers=0),
            Community.objects.create(vkid=3, deactivated=False, ctype=Community.TYPE_CLOSED_GROUP, followers=0),
            Community.objects.create(vkid=4, deactivated=False, ctype=Community.TYPE_PRIVATE_GROUP, followers=0),
            Community.objects.create(vkid=5, deactivated=True, ctype=Community.TYPE_PUBLIC_PAGE, followers=0),
            Community.objects.create(vkid=6, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE, followers=None),
        ]
        wu = WallUpdater(None)
        wu._load_accessible_communities(len(communities))
        self.assertEqual(
            sorted(c.vkid for c in wu._communities),
            [1, 2]
        )

    def test_priority_of_community_depends_on_followers_num(self):
        other_attrs = dict(deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE)
        communities = [
            Community(vkid=1, followers=0, **other_attrs),
            Community(vkid=2, followers=20, **other_attrs),
            Community(vkid=3, followers=10, **other_attrs),
        ]
        self.assertEqual(
            [c.vkid for c in sorted(communities, key=WallUpdater._priority_of_community)],
            [1, 3, 2]
        )

    def test_new_communities_have_highest_priority(self):
        other_attrs = dict(deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE, followers=0)
        dt = timezone.now()
        communities = [
            Community(vkid=1, wall_checked_at=dt, **other_attrs),
            Community(vkid=2, **other_attrs),
            Community(vkid=3, wall_checked_at=dt, **other_attrs),
        ]
        self.assertEqual(
            sorted(communities, key=WallUpdater._priority_of_community)[-1].vkid,
            2
        )

    def test_update_time_is_more_important_than_followers_num(self):
        other_attrs = dict(deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE)
        dt = timezone.now()
        communities = [
            Community(vkid=1, followers=0, wall_checked_at=dt + TimeDelta(hours=1), **other_attrs),
            Community(vkid=2, followers=20, wall_checked_at=dt, **other_attrs),
            Community(vkid=3, followers=10, wall_checked_at=dt + TimeDelta(hours=2), **other_attrs),
        ]
        self.assertEqual(
            [c.vkid for c in sorted(communities, key=WallUpdater._priority_of_community)],
            [3, 1, 2]
        )

    def test_current_community_has_highest_priority(self):
        other_attrs = dict(deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE)
        dt = timezone.now()
        communities = [
            Community.objects.create(vkid=1, followers=0, wall_checked_at=dt + TimeDelta(hours=1), **other_attrs),
            Community.objects.create(vkid=2, followers=20, wall_checked_at=dt, **other_attrs),
            Community.objects.create(vkid=3, followers=10, wall_checked_at=dt + TimeDelta(hours=2), **other_attrs),
        ]
        wu = WallUpdater(None)
        wu._load_accessible_communities(len(communities))
        self.assertEqual(wu._current_community().vkid, 2)

    def test_content_attachments_parsing(self):
        data = """
        {
            "id":34253456,
            "from_id":-57846937,
            "owner_id":-57846937,
            "text":"test text",
            "attachments":[
                {
                    "type":"photo",
                    "photo":{
                        "id":235534,
                        "album_id":-7,
                        "owner_id":-57846937,
                        "user_id":100,
                        "photo_75":"https:\/\/pp.userapi.com\/path75.jpg",
                        "photo_130":"https:\/\/pp.userapi.com\/path130.jpg",
                        "photo_604":"https:\/\/pp.userapi.com\/path604.jpg",
                        "photo_807":"https:\/\/pp.userapi.com\/path807.jpg",
                        "photo_1280":"https:\/\/pp.userapi.com\/path1280.jpg",
                        "width":1074,
                        "height":478,
                        "text":"",
                        "date":1528820156,
                        "post_id":34253456
                    }
                },
                {
                    "type":"video",
                    "video":{
                        "id":234325,
                        "owner_id":-57846937,
                        "title":"test title",
                        "duration":35,
                        "description":"",
                        "date":1532160124,
                        "comments":96,
                        "views":314612,
                        "width":640,
                        "height":640,
                        "photo_130":"https:\/\/pp.userapi.com\/path130.jpg",
                        "photo_320":"https:\/\/pp.userapi.com\/path320.jpg",
                        "photo_800":"https:\/\/pp.userapi.com\/path800.jpg",
                        "can_add":1
                    }
                }
            ]
        }
        """
        data = json.loads(data)
        content = WallUpdater._parse_content(data)
        self.assertEqual(content, [
            {
                "from_id": -57846937,
                "text": "test text",
                "attachments": [
                    {
                        "type": "photo",
                        "photo": r"https://pp.userapi.com/path604.jpg",
                    },
                    {
                        "type": "video",
                        "title": "test title",
                        "preview": r"https://pp.userapi.com/path800.jpg",
                        "duration": 35,
                        "views": 314612,
                    },
                ]
            }
        ])

    def test_content_copy_history_parsing(self):
        data = """
        {
            "id":34253456,
            "from_id":-57846937,
            "owner_id":-333,
            "text":"text1",
            "copy_history": [
                {
                    "id":1,
                    "from_id":-1,
                    "owner_id":-1,
                    "text":"text2"
                },
                {
                    "id":2,
                    "from_id":-2,
                    "owner_id":-22,
                    "text":"text3"
                }
            ]
        }
        """
        data = json.loads(data)
        content = WallUpdater._parse_content(data)
        self.assertEqual(content, [
            {
                "from_id": -57846937,
                "owner_id": -333,
                "text": "text1",
            },
            {
                "from_id": -1,
                "text": "text2",
            },
            {
                "from_id": -2,
                "owner_id": -22,
                "text": "text3",
            },
        ])


class LinksParsingTests(SimpleTestCase):

    def test_borders_of_links(self):
        text_2_link = [
            (r"""aaa.test.com""", r"""aaa.test.com"""),
            (r"""aaaяtest.com""", r"""aaaяtest.com"""),
            (r"""aaaёtest.com""", r"""aaaёtest.com"""),
            (r"""aaaґtest.com""", r"""aaaґtest.com"""),
            (r"""aaaєtest.com""", r"""aaaєtest.com"""),
            (r"""aaastest.com""", r"""aaastest.com"""),

            (r"""test.com.aaa""", r"""test.com.aaa"""),
            (r"""test.com,aaa""", r"""test.com"""),
            (r"""test.com7aaa""", None),
            (r"""test.com-aaa""", None),
            (r"""test.com_aaa""", r"""test.com"""),
            (r"""test.com/aaa""", r"""test.com/aaa"""),
            (r"""test.com\aaa""", r"""test.com"""),
            (r"""test.com+aaa""", r"""test.com"""),
            (r"""test.com=aaa""", r"""test.com"""),
            (r"""test.com*aaa""", r"""test.com"""),
            (r"""test.com;aaa""", r"""test.com"""),
            (r"""test.com:aaa""", r"""test.com"""),
            (r"""test.com"aaa""", r"""test.com"""),
            (r"""test.com'aaa""", r"""test.com"""),
            (r"""test.com`aaa""", r"""test.com"""),
            (r"""test.com~aaa""", r"""test.com"""),
            (r"""test.com!aaa""", r"""test.com"""),
            (r"""test.com@aaa""", r"""test.com"""),
            (r"""test.com#aaa""", r"""test.com#aaa"""),
            (r"""test.com№aaa""", r"""test.com"""),
            (r"""test.com$aaa""", r"""test.com"""),
            (r"""test.com%aaa""", r"""test.com"""),
            (r"""test.com^aaa""", r"""test.com"""),
            (r"""test.com&aaa""", r"""test.com"""),
            (r"""test.com?aaa""", r"""test.com?aaa"""),
            (r"""test.com<aaa""", r"""test.com"""),
            (r"""test.com>aaa""", r"""test.com"""),
            (r"""test.com(aaa""", r"""test.com"""),
            (r"""test.com)aaa""", r"""test.com"""),
            (r"""test.com[aaa""", r"""test.com"""),
            (r"""test.com]aaa""", r"""test.com"""),
            (r"""test.com{aaa""", r"""test.com"""),
            (r"""test.com}aaa""", r"""test.com"""),
            (r"""test.com|aaa""", r"""test.com"""),
            (r"""test.comйaaa""", None),
            (r"""test.comщaaa""", None),
            (r"""test.comьaaa""", None),
            (r"""test.comъaaa""", None),
            (r"""test.comыaaa""", None),
            (r"""test.comяaaa""", None),
            (r"""test.comёaaa""", r"""test.com"""),
            (r"""test.comґaaa""", r"""test.com"""),
            (r"""test.comєaaa""", r"""test.com"""),
            (r"""test.comsaaa""", None),

            (r"""test.com/.aaa""", r"""test.com/.aaa"""),
            (r"""test.com/,aaa""", r"""test.com/,aaa"""),
            (r"""test.com/7aaa""", r"""test.com/7aaa"""),
            (r"""test.com/-aaa""", r"""test.com/-aaa"""),
            (r"""test.com/_aaa""", r"""test.com/_aaa"""),
            (r"""test.com//aaa""", r"""test.com//aaa"""),
            (r"""test.com/\aaa""", r"""test.com/\aaa"""),
            (r"""test.com/+aaa""", r"""test.com/+aaa"""),
            (r"""test.com/=aaa""", r"""test.com/=aaa"""),
            (r"""test.com/*aaa""", r"""test.com/"""),
            (r"""test.com/;aaa""", r"""test.com/;aaa"""),
            (r"""test.com/:aaa""", r"""test.com/:aaa"""),
            (r"""test.com/"aaa""", r"""test.com/"aaa"""),
            (r"""test.com/'aaa""", r"""test.com/'aaa"""),
            (r"""test.com/`aaa""", r"""test.com/"""),
            (r"""test.com/~aaa""", r"""test.com/~aaa"""),
            (r"""test.com/!aaa""", r"""test.com/!aaa"""),
            (r"""test.com/@aaa""", r"""test.com/@aaa"""),
            (r"""test.com/#aaa""", r"""test.com/#aaa"""),
            (r"""test.com/№aaa""", r"""test.com/"""),
            (r"""test.com/$aaa""", r"""test.com/$aaa"""),
            (r"""test.com/%aaa""", r"""test.com/%aaa"""),
            (r"""test.com/^aaa""", r"""test.com/"""),
            (r"""test.com/&aaa""", r"""test.com/&aaa"""),
            (r"""test.com/?aaa""", r"""test.com/?aaa"""),
            (r"""test.com/<aaa""", r"""test.com/<aaa"""),
            (r"""test.com/>aaa""", r"""test.com/>aaa"""),
            (r"""test.com/(aaa""", r"""test.com/"""),
            (r"""test.com/)aaa""", r"""test.com/"""),
            (r"""test.com/[aaa""", r"""test.com/"""),
            (r"""test.com/]aaa""", r"""test.com/"""),
            (r"""test.com/{aaa""", r"""test.com/"""),
            (r"""test.com/}aaa""", r"""test.com/"""),
            (r"""test.com/|aaa""", r"""test.com/"""),
            (r"""test.com/яaaa""", r"""test.com/яaaa"""),
            (r"""test.com/ёaaa""", r"""test.com/ёaaa"""),
            (r"""test.com/ґaaa""", r"""test.com/ґaaa"""),
            (r"""test.com/єaaa""", r"""test.com/єaaa"""),
            (r"""test.com/saaa""", r"""test.com/saaa"""),

            (r"""test.com/z.aaa""", r"""test.com/z.aaa"""),
            (r"""test.com/z,aaa""", r"""test.com/z,aaa"""),
            (r"""test.com/z7aaa""", r"""test.com/z7aaa"""),
            (r"""test.com/z-aaa""", r"""test.com/z-aaa"""),
            (r"""test.com/z_aaa""", r"""test.com/z_aaa"""),
            (r"""test.com/z/aaa""", r"""test.com/z/aaa"""),
            (r"""test.com/z\aaa""", r"""test.com/z\aaa"""),
            (r"""test.com/z+aaa""", r"""test.com/z+aaa"""),
            (r"""test.com/z=aaa""", r"""test.com/z=aaa"""),
            (r"""test.com/z*aaa""", r"""test.com/z"""),
            (r"""test.com/z;aaa""", r"""test.com/z;aaa"""),
            (r"""test.com/z:aaa""", r"""test.com/z:aaa"""),
            (r"""test.com/z"aaa""", r"""test.com/z"aaa"""),
            (r"""test.com/z'aaa""", r"""test.com/z'aaa"""),
            (r"""test.com/z`aaa""", r"""test.com/z"""),
            (r"""test.com/z~aaa""", r"""test.com/z~aaa"""),
            (r"""test.com/z!aaa""", r"""test.com/z!aaa"""),
            (r"""test.com/z@aaa""", r"""test.com/z@aaa"""),
            (r"""test.com/z#aaa""", r"""test.com/z#aaa"""),
            (r"""test.com/z№aaa""", r"""test.com/z"""),
            (r"""test.com/z$aaa""", r"""test.com/z$aaa"""),
            (r"""test.com/z%aaa""", r"""test.com/z%aaa"""),
            (r"""test.com/z^aaa""", r"""test.com/z"""),
            (r"""test.com/z&aaa""", r"""test.com/z&aaa"""),
            (r"""test.com/z?aaa""", r"""test.com/z?aaa"""),
            (r"""test.com/z<aaa""", r"""test.com/z<aaa"""),
            (r"""test.com/z>aaa""", r"""test.com/z>aaa"""),
            (r"""test.com/z(aaa""", r"""test.com/z"""),
            (r"""test.com/z)aaa""", r"""test.com/z"""),
            (r"""test.com/z[aaa""", r"""test.com/z"""),
            (r"""test.com/z]aaa""", r"""test.com/z"""),
            (r"""test.com/z{aaa""", r"""test.com/z"""),
            (r"""test.com/z}aaa""", r"""test.com/z"""),
            (r"""test.com/z|aaa""", r"""test.com/z"""),
            (r"""test.com/zяaaa""", r"""test.com/zяaaa"""),
            (r"""test.com/zёaaa""", r"""test.com/zёaaa"""),
            (r"""test.com/zґaaa""", r"""test.com/zґaaa"""),
            (r"""test.com/zєaaa""", r"""test.com/zєaaa"""),
            (r"""test.com/zsaaa""", r"""test.com/zsaaa"""),

            (r"""-test.com""", r"""-test.com"""),
            (r"""_test.com""", r"""_test.com"""),
            (r"""%test.com""", r"""test.com"""),
            (r""",test.com""", r"""test.com"""),
            (r"""a.test.com""", r"""a.test.com"""),
            (r"""я.test.com""", r"""я.test.com"""),
            (r"""ё.test.com""", r"""ё.test.com"""),
            (r"""7.test.com""", r"""7.test.com"""),
            (r"""-.test.com""", r"""-.test.com"""),
            (r"""_.test.com""", r"""_.test.com"""),
            (r"""ґ.test.com""", r"""ґ.test.com"""),
            (r"""є.test.com""", r"""є.test.com"""),
            (r"""і.test.com""", r"""і.test.com"""),
            (r"""ї.test.com""", r"""ї.test.com"""),

            (r"""test@test.com""", None),

            ('\ntest.com\n', 'test.com'),
            ('\nhttps://test.com\n', 'https://test.com'),
        ]
        for text, link in text_2_link:
            found_links = WallUpdater._find_links(text)
            if link is None:
                self.assertEqual(
                    len(found_links), 0,
                    'found {0} in {1} instead nothing'.format(found_links, text))
            else:
                self.assertEqual(
                    len(found_links), 1,
                    'found {0} in {1} instead {2}'.format(found_links, text, link))
                self.assertEqual(
                    found_links[0], link,
                    'found {0} in {1} instead {2}'.format(found_links, text, link))

    def test_available_symbols_in_domain(self):
        links = [
            'abcdefghijklmnopqrstuvwxyz.com',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ.COM',
            'абвгдеёжзийклмнопрстуфхцчшщъыьэюя.рус',
            'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ.РУС',
            'ґєії.укр',
            'ҐЄІЇ.УКР',
            'AbCвДеЁжҐєІї.org',
            'тест-_.7.ru',
        ]
        for link in links:
            found_links = WallUpdater._find_links(link)
            self.assertEqual(
                len(found_links), 1,
                'found {0} in {1} instead {1}'.format(found_links, link))
            self.assertEqual(found_links[0], link)

    def test_available_symbols_in_path(self):
        link = r'''test.com/.,7-_/\+=;:"'~!@#$%&?<>яёґєsЯЁҐЄS'''
        found_links = WallUpdater._find_links(link)
        self.assertEqual(
            len(found_links), 1,
            'found {0} in {1} instead {1}'.format(found_links, link))
        self.assertEqual(found_links[0], link)

    def test_excluded_domains(self):
        links = [
            'vk.com',
            'm.vk.com',
            '0.vk.com',
        ]
        for link in links:
            found_links = WallUpdater._find_links(link)
            self.assertEqual(
                len(found_links), 0,
                'found {0} in {1} instead nothing'.format(found_links, link))

        link = 'vk.com.com'
        found_links = WallUpdater._find_links(link)
        self.assertEqual(
            len(found_links), 1,
            'found {0} in {1} instead {1}'.format(found_links, link))
        self.assertEqual(found_links[0], 'vk.com.com')
