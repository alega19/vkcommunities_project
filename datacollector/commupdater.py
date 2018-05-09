import logging
from datetime import timedelta as TimeDelta
from threading import Thread, Event

from django.utils import timezone

from communities.models import Community
from datacollector.vkapi import COMMUNITIES_PER_REQUEST, TryAgain


COMMUNITY_UPDATE_PERIOD = TimeDelta(hours=12)
COMMUNITIES_BUFFER_MAX_LENGTH = 20 * COMMUNITIES_PER_REQUEST


logger = logging.getLogger(__name__)


class VkApiParsingError(Exception):
    pass


class CommunitiesUpdater(Thread):

    def __init__(self, vkapi):
        super().__init__()
        self._vkapi = vkapi
        self._stop_event = Event()
        self._communities_buffer = []
        self._check_time = None

    def stop(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set():
            try:
                self._loop()
            except TryAgain:
                self._sleep(1)
            except Exception as err:
                logger.exception(err)
                break
        self._stop_event.clear()

    def _loop(self):
        if self._communities_buffer:
            self._sleep_until_check_begins()
            self._update_communities()
        else:
            self._load_communities()

    def _sleep_until_check_begins(self):
        last_check_time = self._communities_buffer[0].checked_at
        if last_check_time is None or \
                self._communities_buffer[-1].checked_at is None:  # because ORM cannot use 'NULLS FIRST'
            return
        next_check_time = last_check_time + COMMUNITY_UPDATE_PERIOD
        delay = (next_check_time - timezone.now()).total_seconds()
        if delay < 0:
            logger.warning('CommunitiesUpdater is %s seconds late', -delay)
        elif delay > 0:
            self._sleep(delay)

    def _sleep(self, seconds):
        self._stop_event.wait(timeout=seconds)

    def _update_communities(self):
        communities = self._communities_buffer[:COMMUNITIES_PER_REQUEST]
        items = self._request(communities)
        vkid2data = {item['id']: item for item in items}
        for comm in communities:
            data = vkid2data.get(comm.vkid)
            self._update_community(comm, data)
            logger.info('community(id=%s) has been updated', comm.vkid)
        self._communities_buffer = self._communities_buffer[COMMUNITIES_PER_REQUEST:]

    def _request(self, communities):
        ids = [c.vkid for c in communities]
        items = self._vkapi.get_communities(ids)
        self._check_time = timezone.now()
        return items

    def _update_community(self, comm, data):
        comm.deactivated = self._parse_deactivated(data)
        comm.ctype = self._parse_type(data)
        comm.verified = self._parse_verified(data)
        comm.age_limit = self._parse_age_limit(data)
        comm.name = data.get('name', '')
        comm.description = data.get('description', '')
        comm.followers = data.get('members_count')
        comm.status = data.get('status', '')
        comm.icon50url = data.get('photo_50', '')
        comm.icon100url = data.get('photo_100', '')
        comm.checked_at = self._check_time
        comm.save()

    @staticmethod
    def _parse_deactivated(data):
        return 'deactivated' in data

    @staticmethod
    def _parse_type(data):
        type_ = data['type']

        if type_ == 'page':
            return Community.TYPE_PUBLIC_PAGE

        if type_ != 'group':
            raise VkApiParsingError('unexpected value of a parameter type = {0}'.format(type_))

        closed = data['is_closed']
        if closed == 0:
            return Community.TYPE_OPEN_GROUP
        if closed == 1:
            return Community.TYPE_CLOSED_GROUP
        if closed == 2:
            return Community.TYPE_PRIVATE_GROUP
        raise VkApiParsingError('unexpected value of a parameter is_closed = {0}'.format(closed))

    @staticmethod
    def _parse_verified(data):
        verified = data.get('verified')
        if verified is None:
            return None
        if verified == 0:
            return False
        if verified == 1:
            return True
        raise VkApiParsingError('unexpected value of a parameter verified = {0}'.format(verified))

    @staticmethod
    def _parse_age_limit(data):
        age_limits = data.get('age_limits')
        if age_limits is None:
            return Community.AGELIMIT_UNKNOWN
        if age_limits == 1:
            return Community.AGELIMIT_NONE
        if age_limits == 2:
            return Community.AGELIMIT_16
        if age_limits == 3:
            return Community.AGELIMIT_18
        raise VkApiParsingError('unexpected value of a parameter age_limits = {0}'.format(age_limits))

    def _load_communities(self):
        communities = Community.objects.order_by('checked_at')[:COMMUNITIES_BUFFER_MAX_LENGTH]
        self._communities_buffer = list(communities)
        if not self._communities_buffer:
            raise RuntimeError('no communities in the database')
