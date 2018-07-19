from datetime import timedelta as TimeDelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from communities.models import Community
from ..commupdater import CommunitiesUpdater, VkApiParsingError, COMMUNITY_UPDATE_PERIOD


class CommunitiesUpdaterTest(TestCase):

    def test_parsing_error_does_not_stop_work(self):
        cu = CommunitiesUpdater(None)
        cu._communities_buffer = [Mock()] * 3
        with patch('datacollector.commupdater.COMMUNITIES_PER_REQUEST', new=3),\
                patch.object(cu, '_request') as _request,\
                patch.object(cu, '_update_community') as _update_community:
            _request.return_value = dict()
            _update_community.side_effect = [Mock(), VkApiParsingError, Mock()]
            cu._update_communities()
            self.assertEqual(_update_community.call_count, 3)

    def test_load_communities(self):
        other_attrs = dict(deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE)
        dt = timezone.now()
        Community.objects.create(vkid=1, checked_at=dt + TimeDelta(hours=2), **other_attrs),
        Community.objects.create(vkid=2, checked_at=dt, **other_attrs),
        Community.objects.create(vkid=3, **other_attrs),
        Community.objects.create(vkid=4, checked_at=dt + TimeDelta(hours=1), **other_attrs),
        cu = CommunitiesUpdater(None)
        with patch('datacollector.commupdater.COMMUNITIES_BUFFER_MAX_LENGTH', new=3):
            cu._load_communities()
            self.assertEqual(
                [c.vkid for c in cu._communities_buffer],
                [3, 2, 4]
            )

    def test_sleep_until_check_begins(self):
        now = timezone.now()
        cu = CommunitiesUpdater(None)
        cu._communities_buffer = [Community(vkid=1, deactivated=False, ctype=Community.TYPE_PUBLIC_PAGE,
                                  checked_at=now - COMMUNITY_UPDATE_PERIOD + TimeDelta(seconds=42))]
        with patch('django.utils.timezone.now', return_value=now),\
                patch.object(cu, '_sleep') as _sleep:
            cu._sleep_until_check_begins()
            self.assertEqual(_sleep.call_args, [(42,)])
