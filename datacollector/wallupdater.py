import logging
import re
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from threading import Thread, Event

from django.db import transaction
from django.db.models import FloatField, Count, F
from django.db.models.functions import Cast
from django.utils import timezone

import pytz

from communities.models import Community, Post
from datacollector.vkapi import REQUEST_DELAY_PER_TOKEN_FOR_WALL, TryAgain
from .errors import VkApiParsingError
from .models import Median
from .utils.tld import LATIN_TLD_LIST, CYRILLIC_TLD_LIST


WALL_UPDATE_PERIOD = 23 * 3600
DEFAULT_UPDATE_DURATION = REQUEST_DELAY_PER_TOKEN_FOR_WALL
MIN_PERIOD_FOR_STATS = TimeDelta(seconds=300)

MIN_POSTS_NUM_FOR_STATS = 5
MIN_LIFETIME_OF_POST = TimeDelta(hours=24)
PERIOD_FOR_POSTS_STATS = TimeDelta(days=7)


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
        logger.info('started')
        while not self._stop_event.is_set():
            try:
                self._loop()
            except TryAgain:
                self._sleep(1)
            except Exception as err:
                logger.exception(err)
                self._sleep(10)
        self._stop_event.clear()
        logger.info('stopped')

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
                    try:
                        self._save_post(comm, p, check_time)
                    except VkApiParsingError as err:
                        logger.error(repr(err))

            posts_stats = Post.objects.filter(
                community_id=comm,
                published_at__gt=check_time - PERIOD_FOR_POSTS_STATS - MIN_LIFETIME_OF_POST,
                checked_at__gte=F('published_at') + MIN_LIFETIME_OF_POST,
                views__gt=0
            ).aggregate(
                views_per_post=Median('views'),
                likes_per_view=Median(Cast('likes', FloatField()) / Cast('views', FloatField())),
                count=Count('*')
            )
            if posts_stats['count'] >= MIN_POSTS_NUM_FOR_STATS:
                comm.views_per_post = posts_stats['views_per_post']
                comm.likes_per_view = posts_stats['likes_per_view']
            else:
                comm.views_per_post = None
                comm.likes_per_view = None

            comm.wall_checked_at = check_time
            comm.save(update_fields=['wall_checked_at', 'views_per_post', 'likes_per_view'])

        self._updated_walls += 1

    def _save_post(self, comm, data, check_time):
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
            likes=self._parse_likes(comm, data),
            shares=data['reposts']['count'],
            comments=data['comments']['count'],
            marked_as_ads=data['marked_as_ads'] == 1,
            links=len(self._parse_links(data))
        ).save()

    @staticmethod
    def _parse_likes(comm, data):
        likes = data.get('likes')
        if likes is None:
            raise VkApiParsingError(
                'post(id={0}) of community(id={1}) has no likes counter'.format(data['id'], comm.vkid))
        return likes['count']

    def _parse_links(self, data):
        links = set()
        found_links = self._find_links(data['text'])
        copy_history = data.get('copy_history', [])
        for post_data in copy_history:
            found_links.extend(self._find_links(post_data['text']))
        for link in found_links:
            if not link.startswith('https://'):
                link = 'http://' + link
            links.add(link)
        return links

    _TLD_LIST = sorted(LATIN_TLD_LIST + CYRILLIC_TLD_LIST, reverse=True)
    _REGEXP = re.compile(
        r'''((?i:https://)?)'''
        r'''(@)?'''  # to exclude emails
        r'''((?:[-_0-9a-zA-Zа-яёґєіїА-ЯЁҐЄІЇ]+\.)+)'''
        r'''((?i:{}))'''.format('|'.join(_TLD_LIST)) + r'''(?![-0-9a-zA-Zа-яА-Я])'''
        r'''([/?#][-_.,/\\+=;:"'~!@#$%&?<>0-9a-zA-Zа-яёґєіїА-ЯЁҐЄІЇ]*)?'''
    )
    _EXCLUDED_DOMAINS = ('vk.com', 'm.vk.com', '0.vk.com')

    @classmethod
    def _find_links(cls, text):
        links = []
        for protocol, at, name, tld, path in cls._REGEXP.findall(text):
            domain = name + tld
            if not at and domain not in cls._EXCLUDED_DOMAINS:
                links.append(protocol + domain + path)
        return links

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
            'followers', 'wall_checked_at', 'views_per_post', 'likes_per_view'
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
