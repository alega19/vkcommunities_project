from datetime import timedelta as TimeDelta

from django.test import SimpleTestCase
from django.utils import timezone

from ..forms import CommunitySearchForm, PostSearchForm


class CommunitySearchFormTest(SimpleTestCase):

    def test_form_requires_only_sort_field(self):
        form = CommunitySearchForm({})
        self.assertFalse(form.is_valid())
        form = CommunitySearchForm({'sort_by': 'followers'})
        self.assertTrue(form.is_valid())

    def test_followers_cannot_be_negative(self):
        form = CommunitySearchForm({'followers_min': -1, 'sort_by': 'followers'})
        self.assertFalse(form.is_valid())
        form = CommunitySearchForm({'followers_max': -1, 'sort_by': 'followers'})
        self.assertFalse(form.is_valid())

    def test_views_per_post_cannot_be_negative(self):
        form = CommunitySearchForm({'views_per_post_min': -1, 'sort_by': 'followers'})
        self.assertFalse(form.is_valid())
        form = CommunitySearchForm({'views_per_post_max': -1, 'sort_by': 'followers'})
        self.assertFalse(form.is_valid())

    def test_likes_per_view_cannot_be_negative(self):
        form = CommunitySearchForm({'likes_per_view_min': -1, 'sort_by': 'followers'})
        self.assertFalse(form.is_valid())
        form = CommunitySearchForm({'likes_per_view_max': -1, 'sort_by': 'followers'})
        self.assertFalse(form.is_valid())

    def test_followers_range(self):
        form = CommunitySearchForm({'followers_min': 11, 'followers_max': 10, 'sort_by': 'followers'})
        self.assertFalse(form.is_valid())

    def test_views_per_post_range(self):
        form = CommunitySearchForm({'views_per_post_min': 11, 'views_per_post_max': 10, 'sort_by': 'followers'})
        self.assertFalse(form.is_valid())

    def test_likes_per_view_range(self):
        form = CommunitySearchForm({'likes_per_view_min': 11, 'likes_per_view_max': 10, 'sort_by': 'followers'})
        self.assertFalse(form.is_valid())


class PostSearchFormTest(SimpleTestCase):

    def test_form_requires_only_sort_field(self):
        form = PostSearchForm({})
        self.assertFalse(form.is_valid())
        form = PostSearchForm({'sort_by': 'published_at'})
        self.assertTrue(form.is_valid())

    def test_views_cannot_be_negative(self):
        form = PostSearchForm({'views_min': -1, 'sort_by': 'published_at'})
        self.assertFalse(form.is_valid())
        form = PostSearchForm({'views_max': -1, 'sort_by': 'published_at'})
        self.assertFalse(form.is_valid())

    def test_likes_per_view_cannot_be_negative(self):
        form = PostSearchForm({'likes_per_view_min': -1, 'sort_by': 'published_at'})
        self.assertFalse(form.is_valid())
        form = PostSearchForm({'likes_per_view_max': -1, 'sort_by': 'published_at'})
        self.assertFalse(form.is_valid())

    def test_date_range(self):
        dt = timezone.now()
        dt_before = dt - TimeDelta(seconds=1)
        form = PostSearchForm({'date_min': dt, 'date_max': dt_before, 'sort_by': 'published_at'})
        self.assertFalse(form.is_valid())

    def test_views_per_post_range(self):
        form = PostSearchForm({'views_min': 11, 'views_max': 10, 'sort_by': 'published_at'})
        self.assertFalse(form.is_valid())

    def test_likes_per_view_range(self):
        form = PostSearchForm({'likes_per_view_min': 11, 'likes_per_view_max': 10, 'sort_by': 'published_at'})
        self.assertFalse(form.is_valid())
