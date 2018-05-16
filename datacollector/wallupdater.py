import logging
from datetime import timedelta as TimeDelta
from threading import Thread, Event

from django.db import transaction
from django.utils import timezone

from communities.models import Community, WallCheckingLog
from datacollector.vkapi import REQUEST_DELAY_PER_TOKEN_FOR_WALL, TryAgain


WALL_UPDATE_PERIOD = 23 * 3600
DEFAULT_UPDATE_DURATION = REQUEST_DELAY_PER_TOKEN_FOR_WALL
MIN_PERIOD_FOR_STATS = TimeDelta(seconds=120)


logger = logging.getLogger(__name__)


class WallUpdater(Thread):

    def __init__(self, vkapi):
        super().__init__()
        self._vkapi = vkapi
        self._stop_event = Event()
        self._period_start = None
        self._updated_walls = 0
        self._communities = []  # the last element is first in queue (has a higher priority)
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
        if self._communities and (timezone.now() - self._period_start) < MIN_PERIOD_FOR_STATS:
            self._update_wall()
        else:
            self._load_communities()

    def _sleep(self, seconds):
        self._stop_event.wait(timeout=seconds)

    def _update_wall(self):
        comm = self._communities[-1]
        check_time = timezone.now()
        posts = self._vkapi.get_community_wall(comm.vkid)
        self._communities.pop()
        if posts is None:
            logger.info('cannot get the wall of the community(id=%s)', comm.vkid)
            return
        print(comm.vkid, 'OK:', len(posts))
        WallCheckingLog.objects.create(community=comm, checked_at=check_time)
        self._updated_walls += 1

    def _load_communities(self):
        if self._updated_walls == 0:
            update_duration = DEFAULT_UPDATE_DURATION
        else:
            update_duration = (timezone.now() - self._period_start).total_seconds() / self._updated_walls

        self._period_start = timezone.now()
        self._updated_walls = 0

        num = int(WALL_UPDATE_PERIOD / update_duration)
        print(num, update_duration)
        with transaction.atomic():
            communities = Community.objects.filter(
                deactivated=False,
                ctype__in=(Community.TYPE_PUBLIC_PAGE, Community.TYPE_OPEN_GROUP),
                followers__isnull=False,
            ).order_by(
                '-followers'
            ).only(
                'vkid'
            )[:num]

            last_wall_checks = WallCheckingLog.objects.order_by(
                'community', '-checked_at'
            ).distinct(
                'community'
            ).values_list(
                'community', 'checked_at'
            )
            last_wall_checks = dict(last_wall_checks)

        for c in communities:
            c.wall_checked_at = last_wall_checks.get(c.vkid)

        now = timezone.now()
        self._communities = sorted(
            communities,
            key=lambda c: c.wall_checked_at or now,  # new communities have the lowest priority
            reverse=True
        )
