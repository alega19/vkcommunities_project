from django.test import TestCase

from ..models import Community


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
