from django.test import TestCase

from ..models import Community


class ExtraQuerySetTest(TestCase):

    def test_sort_by(self):
        Community.objects.create(vkid=1, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE)
        Community.objects.create(vkid=2, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE)
        Community.objects.create(vkid=3, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE)
        Community.objects.create(vkid=4, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE)
        self.assertQuerysetEqual(Community.available.sort_by('vkid', True), [4, 3, 2, 1], lambda c: c.vkid)

    def test_exclude_nulls(self):
        Community.objects.create(vkid=1, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE)
        Community.objects.create(vkid=2, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE, followers=42)
        self.assertQuerysetEqual(Community.available.exclude_nulls('followers'), [2], lambda c: c.vkid)

    def test_filter_ignoring_nonetype(self):
        Community.objects.create(vkid=1, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE, followers=11)
        Community.objects.create(vkid=2, deactivated=False, ctype=Community.TYPE_OPEN_GROUP, followers=22)
        Community.objects.create(vkid=3, deactivated=False, ctype=Community.TYPE_CLOSED_GROUP)
        self.assertQuerysetEqual(
            Community.available.filter_ignoring_nonetype(
                ctype__in=(Community.TYPE_PUBLIC_PAGE, Community.TYPE_CLOSED_GROUP),
                followers=None,
            ).order_by('vkid'),
            [1, 3],
            lambda c: c.vkid
        )


class CommunityTest(TestCase):

    def test_vk_url(self):
        public_page = Community(vkid=1, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE)
        self.assertEqual(public_page.vk_url(), 'https://vk.com/public1')

        open_group = Community(vkid=1, deactivated=False, ctype=Community.TYPE_OPEN_GROUP)
        self.assertEqual(open_group.vk_url(), 'https://vk.com/club1')

        closed_group = Community(vkid=1, deactivated=False, ctype=Community.TYPE_CLOSED_GROUP)
        self.assertEqual(closed_group.vk_url(), 'https://vk.com/club1')

        private_group = Community(vkid=1, deactivated=False, ctype=Community.TYPE_PRIVATE_GROUP)
        self.assertEqual(private_group.vk_url(), 'https://vk.com/club1')

    def test_only_private_and_deactivated_groups_are_not_available(self):
        Community.objects.create(vkid=1, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE)
        Community.objects.create(vkid=2, deactivated=False, ctype=Community.TYPE_OPEN_GROUP)
        Community.objects.create(vkid=3, deactivated=False, ctype=Community.TYPE_CLOSED_GROUP)
        Community.objects.create(vkid=4, deactivated=False, ctype=Community.TYPE_PRIVATE_GROUP)
        Community.objects.create(vkid=5, deactivated=True, ctype=Community.TYPE_PUBLIC_PAGE)
        Community.objects.create(vkid=6, deactivated=True, ctype=Community.TYPE_OPEN_GROUP)
        Community.objects.create(vkid=7, deactivated=True, ctype=Community.TYPE_CLOSED_GROUP)
        Community.objects.create(vkid=8, deactivated=True, ctype=Community.TYPE_PRIVATE_GROUP)
        available_communities = Community.available.order_by('vkid')
        available_community_ids = [c.vkid for c in available_communities]
        self.assertEqual(available_community_ids, [1, 2, 3])
