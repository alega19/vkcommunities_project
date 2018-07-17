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
        self._check_time = None
        self._updated_walls = 0
        self._communities = []  # the last element is first in queue (has a higher priority)

    def _current_community(self):
        return self._communities[-1]

    def _change_current_community(self):
        self._communities.pop()

    def stop(self):
        self._stop_event.set()

    def run(self):
        logger.info('started')
        while not self._stop_event.is_set():
            try:
                self._loop()
            except Exception as err:
                logger.exception(err)
                self._sleep(10)
        self._stop_event.clear()
        logger.info('stopped')

    def _loop(self):
        if not self._communities or self._period_for_statistics_is_over():
            num = self._calculate_communities_per_period()
            self._load_accessible_communities(num)
            self._reset_statistics()
        else:
            posts = self._get_new_posts()
            with transaction.atomic():
                self._update_wall(posts)
                self._update_wall_stats()
            self._change_current_community()

    def _period_for_statistics_is_over(self):
        elapsed = timezone.now() - self._period_start
        return elapsed >= MIN_PERIOD_FOR_STATS

    def _sleep(self, seconds):
        self._stop_event.wait(timeout=seconds)

    def _get_new_posts(self):
        comm = self._current_community()
        while True:
            try:
                self._check_time = timezone.now()
                wall_data = self._vkapi.get_community_wall(comm.vkid)
                break
            except TryAgain:
                self._sleep(1)

        if comm.wall_checked_at is not None:
            planned_check_time = comm.wall_checked_at + TimeDelta(seconds=WALL_UPDATE_PERIOD)
            if self._check_time > planned_check_time:
                logger.warning(
                    'updating the community(id=%s) is %.2f seconds late',
                    comm.vkid,
                    (self._check_time - planned_check_time).total_seconds()
                )

        posts = []
        if wall_data is None:
            logger.warning('cannot get the wall of the community(id=%s)', comm.vkid)
        else:
            logger.info('got %s posts for the community(id=%s)', len(wall_data), comm.vkid)
            for post_data in wall_data:
                try:
                    post = self._parse_post(post_data)
                    posts.append(post)
                except VkApiParsingError as err:
                    logger.error('community(id=%s) post(id=%s): %s', comm.vkid, post_data.get('id'), repr(err))
        return posts

    def _update_wall(self, posts):
        for p in posts:
            p.save()
        self._updated_walls += 1

    def _update_wall_stats(self):
        comm = self._current_community()
        posts_stats = Post.objects.filter(
            community_id=comm,
            published_at__gt=self._check_time - PERIOD_FOR_POSTS_STATS - MIN_LIFETIME_OF_POST,
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

        comm.wall_checked_at = self._check_time
        comm.save(update_fields=['wall_checked_at', 'views_per_post', 'likes_per_view'])

    def _parse_post(self, data):
        return Post(
            community=self._current_community(),
            vkid=self._parse_post_id(data),
            checked_at=self._check_time,
            published_at=self._parse_publish_time(data),
            content=self._parse_content(data),
            views=self._parse_views(data),
            likes=self._parse_likes(data),
            shares=self._parse_shares(data),
            comments=self._parse_comments(data),
            marked_as_ads=self._parse_ads_mark(data),
            links=self._count_links(data)
        )

    @staticmethod
    def _parse_post_id(data):
        id_ = data.get('id')
        if id_ is None:
            raise VkApiParsingError('no a post id')
        return id_

    @staticmethod
    def _parse_publish_time(data):
        timestamp = data.get('date')
        if timestamp is None:
            raise VkApiParsingError('no a post date')
        dt = DateTime.utcfromtimestamp(timestamp)
        return pytz.utc.localize(dt)

    @staticmethod
    def _parse_content(data):
        try:
            content = [data['text']]
            content.extend(p['text'] for p in data.get('copy_history', []))
            return content
        except KeyError:
            raise VkApiParsingError('no text or invalid a copy_history')

    @staticmethod
    def _parse_views(data):
        views_data = data.get('views')
        if views_data is None:
            return None
        return views_data['count']

    @staticmethod
    def _parse_likes(data):
        try:
            return data['likes']['count']
        except KeyError:
            raise VkApiParsingError('no a likes counter')

    @staticmethod
    def _parse_shares(data):
        try:
            return data['reposts']['count']
        except KeyError:
            raise VkApiParsingError('no a shares counter')

    @staticmethod
    def _parse_comments(data):
        try:
            return data['comments']['count']
        except KeyError:
            raise VkApiParsingError('no a comments counter')

    @staticmethod
    def _parse_ads_mark(data):
        return data.get('marked_as_ads') == 1

    def _count_links(self, data):
        try:
            text_list = [data['text']]
            text_list.extend(p['text'] for p in data.get('copy_history', []))
        except KeyError:
            raise VkApiParsingError('no text or invalid a copy_history')
        return sum(
            len(self._find_links(text))
            for text in text_list
        )

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
        """Omits any protocol except HTTPS"""
        links = []
        for protocol, at, name, tld, path in cls._REGEXP.findall(text):
            domain = name + tld
            if not at and domain not in cls._EXCLUDED_DOMAINS:
                links.append(protocol + domain + path)
        return links

    def _calculate_communities_per_period(self):
        if self._updated_walls == 0:
            update_duration = DEFAULT_UPDATE_DURATION
        else:
            elapsed = (timezone.now() - self._period_start).total_seconds()
            update_duration = elapsed / self._updated_walls
        num = int(WALL_UPDATE_PERIOD / update_duration)
        logger.info('calculated: %s communities per period, %.2f seconds per each one', num, update_duration)
        return num

    def _load_accessible_communities(self, num):
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
        logger.info('loaded %s communities', len(self._communities))

    @staticmethod
    def _priority_of_community(comm):
        if comm.wall_checked_at is None:
            time_priority = 0  # new communities have the highest priority
        else:
            time_priority = -comm.wall_checked_at.timestamp()
        return time_priority, comm.followers

    def _reset_statistics(self):
        self._period_start = timezone.now()
        self._updated_walls = 0
