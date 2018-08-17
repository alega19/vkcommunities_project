from urllib.parse import urlencode
from datetime import timedelta as TimeDelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from ..models import Community, CommunityHistory, Post


EMAIL = 'superuser42@example42.com'
PASSWORD = 'itismypassword42'


class CommunityListViewTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create_user(EMAIL, PASSWORD, is_active=True)

    def test_only_authenticated_user_can_access(self):
        resp = self.client.get(reverse('communities:community_list'))
        self.assertNotEqual(resp.status_code, 200)

        self.client.login(email=EMAIL, password=PASSWORD)
        resp = self.client.get(reverse('communities:community_list'))
        self.assertEqual(resp.status_code, 200)

    def test_view_lists_items(self):
        params = dict(deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE, followers=1)
        Community.objects.create(vkid=1, name='comm1', **params)
        Community.objects.create(vkid=2, name='comm2', **params)
        Community.objects.create(vkid=3, name='comm3', **params)
        self.client.login(email=EMAIL, password=PASSWORD)
        resp = self.client.get(reverse('communities:community_list'))
        self.assertContains(resp, 'comm1')
        self.assertContains(resp, 'comm2')
        self.assertContains(resp, 'comm3')

    def test_pagination_is_50(self):
        for vkid in range(51):
            Community.objects.create(vkid=vkid, deactivated=False,
                                     ctype=Community.TYPE_PUBLIC_PAGE, followers=1)
        self.client.login(email=EMAIL, password=PASSWORD)

        resp = self.client.get(reverse('communities:community_list'))
        self.assertTrue('page_obj' in resp.context)
        self.assertEqual(len(resp.context['page_obj']), 50)

        resp = self.client.get(reverse('communities:community_list') + '?p=2')
        self.assertTrue('page_obj' in resp.context)
        self.assertEqual(len(resp.context['page_obj']), 1)


class CommunityDetailViewTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create_user(EMAIL, PASSWORD, is_active=True)
        Community.objects.create(vkid=1, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE,
                                 name='comm1', status='status1', description='desc1')

    def test_only_authenticated_user_can_access(self):
        resp = self.client.get(reverse('communities:community_detail', args=[1]))
        self.assertNotEqual(resp.status_code, 200)

        self.client.login(email=EMAIL, password=PASSWORD)
        resp = self.client.get(reverse('communities:community_detail', args=[1]))
        self.assertEqual(resp.status_code, 200)

    def test_view_shows_details(self):
        self.client.login(email=EMAIL, password=PASSWORD)
        resp = self.client.get(reverse('communities:community_detail', args=[1]))
        self.assertContains(resp, 'comm1')
        self.assertContains(resp, 'status1')
        self.assertContains(resp, 'desc1')

    def test_view_shows_followers_trend(self):
        dt = timezone.now()
        CommunityHistory.objects.create(community_id=1, checked_at=dt, followers=10)
        CommunityHistory.objects.create(community_id=1, checked_at=dt + TimeDelta(hours=1), followers=20)
        CommunityHistory.objects.create(community_id=1, checked_at=dt + TimeDelta(hours=2), followers=30)
        Community.objects.create(vkid=2, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE)
        CommunityHistory.objects.create(community_id=2, checked_at=dt, followers=10)
        self.client.login(email=EMAIL, password=PASSWORD)
        resp = self.client.get(reverse('communities:community_detail', args=[1]))
        self.assertEqual(
            tuple(p['y'] for p in resp.context['followers_history']),
            (10, 20, 30)
        )


class PostListViewTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create_user(EMAIL, PASSWORD, is_active=True)
        Community.objects.create(vkid=1, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE)

    def test_only_authenticated_user_can_access(self):
        resp = self.client.get(reverse('communities:post_list'))
        self.assertNotEqual(resp.status_code, 200)

        self.client.login(email=EMAIL, password=PASSWORD)
        resp = self.client.get(reverse('communities:post_list'))
        self.assertEqual(resp.status_code, 200)

    def test_view_lists_items(self):
        params = dict(community_id=1, published_at=timezone.now(), checked_at=timezone.now(),
                      likes=0, shares=0, comments=0, marked_as_ads=False, links=0)
        Post.objects.create(vkid=1, content=[{'text': 'post1'}], **params)
        Post.objects.create(vkid=2, content=[{'text': 'repost2'}, {'text': 'post2'}], **params)
        self.client.login(email=EMAIL, password=PASSWORD)
        resp = self.client.get(reverse('communities:post_list'))
        self.assertContains(resp, 'post1')
        self.assertContains(resp, 'post2')
        self.assertContains(resp, 'repost2')

    def test_pagination_is_20(self):
        params = dict(community_id=1, published_at=timezone.now(), checked_at=timezone.now(),
                      content=[], likes=0, shares=0, comments=0, marked_as_ads=False, links=0)
        for vkid in range(21):
            Post.objects.create(vkid=vkid, **params)
        self.client.login(email=EMAIL, password=PASSWORD)

        resp = self.client.get(reverse('communities:post_list'))
        self.assertTrue('page_obj' in resp.context)
        self.assertEqual(len(resp.context['page_obj']), 20)

        resp = self.client.get(reverse('communities:post_list') + '?p=2')
        self.assertTrue('page_obj' in resp.context)
        self.assertEqual(len(resp.context['page_obj']), 1)

    def test_search(self):
        params = dict(community_id=1, published_at=timezone.now(), checked_at=timezone.now(),
                      views=0, likes=0, shares=0, comments=0, marked_as_ads=False, links=0)
        Post.objects.create(vkid=1, content=[{'text': 'Мороз и солнце'}, {'text': 'день чудесный'}], **params)
        Post.objects.create(vkid=2, content=[{'text': ''}, {'text': 'день чудесный'}], **params)

        self.client.login(email=EMAIL, password=PASSWORD)
        resp = self.client.get(reverse('communities:post_list') + '?sort_by=published_at&' +
                               urlencode({'search': 'мороз и солнце'}))
        self.assertContains(resp, 'день чудесный', 1)
        resp = self.client.get(reverse('communities:post_list') + '?sort_by=published_at&' +
                               urlencode({'search': 'чудесный'}))
        self.assertContains(resp, 'день чудесный', 2)
