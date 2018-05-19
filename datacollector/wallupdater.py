import logging
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from threading import Thread, Event

from django.db import transaction
from django.utils import timezone

import pytz

from communities.models import Community, Post
from datacollector.vkapi import REQUEST_DELAY_PER_TOKEN_FOR_WALL, TryAgain


WALL_UPDATE_PERIOD = 23 * 3600
DEFAULT_UPDATE_DURATION = REQUEST_DELAY_PER_TOKEN_FOR_WALL
MIN_PERIOD_FOR_STATS = TimeDelta(seconds=300)


logger = logging.getLogger(__name__)


class WallUpdater(Thread):

    def __init__(self, vkapi):
        super().__init__()
        self._vkapi = vkapi
        self._stop_event = Event()
        self._period_start = None
        self._updated_walls = 0
        self._communities = []  # the last element is first in queue (has a higher priority)

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
        if comm.wall_checked_at is not None and\
                comm.wall_checked_at + TimeDelta(seconds=WALL_UPDATE_PERIOD) < check_time:
            logger.warning(
                'updating the community(id=%s) is %s seconds late',
                comm.vkid,
                (check_time - comm.wall_checked_at + TimeDelta(seconds=WALL_UPDATE_PERIOD)).total_seconds())

        with transaction.atomic():
            if posts is None:
                logger.warning('cannot get the wall of the community(id=%s)', comm.vkid)
            elif posts:
                logger.info('got %s posts for the community(id=%s)', len(posts), comm.vkid)
                for p in posts:
                    self._save_post(comm, p, check_time)
            comm.wall_checked_at = check_time
            comm.save(update_fields=['wall_checked_at'])
        self._updated_walls += 1

    @staticmethod
    def _save_post(comm, data, check_time):
        content = [data['text']]
        content.extend(p['text'] for p in data.get('copy_history', []))

        if 'views' in data:
            views = data['views']['count']
        else:
            views = None

        Post(
            community=comm,
            vkid=data['id'],
            checked_at=check_time,
            published_at=pytz.utc.localize(DateTime.utcfromtimestamp(data['date'])),
            content=content,
            views=views,
            likes=data['likes']['count'],
            shares=data['reposts']['count'],
            comments=data['comments']['count'],
            marked_as_ads=data['marked_as_ads'] == 1
        ).save()

    def _load_communities(self):
        if self._updated_walls == 0:
            update_duration = DEFAULT_UPDATE_DURATION
        else:
            update_duration = (timezone.now() - self._period_start).total_seconds() / self._updated_walls

        self._period_start = timezone.now()
        self._updated_walls = 0

        num = int(WALL_UPDATE_PERIOD / update_duration)
        logger.info('loaded %s communities, %s seconds per each one', num, update_duration)
        communities = Community.objects.filter(
            deactivated=False,
            ctype__in=(Community.TYPE_PUBLIC_PAGE, Community.TYPE_OPEN_GROUP),
            followers__isnull=False
        ).order_by(
            '-followers'
        ).only(
            'followers', 'wall_checked_at'
        )[:num]

        self._communities = sorted(
            communities,
            key=self._priority_of_community
        )

    @staticmethod
    def _priority_of_community(comm):
        if comm.wall_checked_at is None:
            time_priority = 0  # new communities have the highest priority
        else:
            time_priority = -comm.wall_checked_at.timestamp()
        return time_priority, comm.followers
