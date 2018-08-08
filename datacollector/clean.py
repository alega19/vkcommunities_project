import time
import logging
from datetime import timedelta as TimeDelta

import django
django.setup()
from django.db import connection

from communities.models import Community, CommunityHistory, Post


POST_MAX_AGE = TimeDelta(days=90)
NON_PROMO_POST_MAX_AGE = TimeDelta(days=15)


logger = logging.getLogger('dbcleaner')


def retry(intervals):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            for interval in intervals:
                try:
                    return fn(*args, **kwargs)
                except Exception:
                    time.sleep(interval)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@retry([300, 600, 600])
def cleanup_non_promo_posts():
    now = django.utils.timezone.now()
    num, _ = Post.objects.filter(
        published_at__lt=now - NON_PROMO_POST_MAX_AGE,
        checked_at__lt=now - TimeDelta(hours=25),  # to avoid blocks in db
        links=0,
        marked_as_ads=False,
    ).delete()
    return num


@retry([300, 600, 600])
def cleanup_posts():
    now = django.utils.timezone.now()
    num, _ = Post.objects.filter(
        published_at__lt=now - POST_MAX_AGE,
        checked_at__lt=now - TimeDelta(hours=25),  # to avoid blocks in db
    ).delete()
    return num


@retry([300, 600, 600])
def cleanup_commhistory():
    now = django.utils.timezone.now()

    num, _ = CommunityHistory.objects.filter(
        checked_at__lte=now - TimeDelta(days=365 * 2),
    ).delete()

    num += CommunityHistory.objects.filter(
        checked_at__lte=now - TimeDelta(days=7),
        checked_at__hour__gte=12,
    ).delete()[0]

    num += CommunityHistory.objects.filter(
        checked_at__range=(now - TimeDelta(days=60), now - TimeDelta(days=30)),
        checked_at__day__in=range(2, 31, 2),
    ).delete()[0]

    num += CommunityHistory.objects.filter(
        checked_at__range=(now - TimeDelta(days=180), now - TimeDelta(days=60)),
    ).exclude(
        checked_at__week_day=2,  # Monday
    ).delete()[0]

    num += CommunityHistory.objects.filter(
        checked_at__lte=now - TimeDelta(days=180),
    ).exclude(
        checked_at__day=1,
    ).delete()[0]

    return num


@retry([300, 600, 600])
def vacuum_analyze(table_name):
    logger.info('vacuum+analyze for "%s" started', table_name)
    c = connection.cursor()
    c.execute('VACUUM ANALYZE {};'.format(table_name))
    logger.info('vacuum+analyze for "%s" finished', table_name)


def main():
    logger.info('cleaning posts started')
    num = cleanup_non_promo_posts()
    num += cleanup_posts()
    logger.info('%s posts deleted', num)

    logger.info('cleaning history rows started')
    num = cleanup_commhistory()
    logger.info('%s history rows deleted', num)

    vacuum_analyze(Post._meta.db_table)
    vacuum_analyze(CommunityHistory._meta.db_table)
    vacuum_analyze(Community._meta.db_table)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception(e)
