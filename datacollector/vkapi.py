import json
import logging
import time
from datetime import timedelta as TimeDelta
from threading import RLock
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from django.utils import timezone

from .models import VkAccount


HTTP_REQUEST_TIMEOUT = 60
MIN_NETWORK_ERRORS_BEFORE_ALARM = 30
MIN_NETWORK_ERRORS_DURATION_BEFORE_ALARM = 60
COMMUNITIES_PER_REQUEST = 500
REQUEST_DELAY_PER_TOKEN = 0.5
REQUEST_DELAY_PER_TOKEN_FOR_WALL = 9


logger = logging.getLogger(__name__)


class VkApiResponseError(Exception):

    def __init__(self, errmsg, errcode):
        super().__init__(errmsg, errcode)
        self.code = errcode

    @classmethod
    def from_response(cls, response):
        errmsg = 'unknown VK API error'
        errcode = None
        err = response.get('error')
        if err:
            errmsg = err.get('error_msg', errmsg)
            errcode = err.get('error_code', errcode)
        return cls(errmsg, errcode)


class TryAgain(Exception):
    pass


class Token:
    def __init__(self, api_key):
        self.key = api_key
        self.last_used = timezone.now()
        self.last_used_for_wall = timezone.now()


class VkApi:

    def __init__(self):
        self._lock = RLock()
        self._tokens = set()
        self._load_tokens()
        self._last_successful_request = timezone.now()
        self._network_errors_count = 0  # since the last successful request

    def _load_tokens(self):
        accounts = VkAccount.objects.filter(enabled=True)
        for acc in accounts:
            self._tokens.add(Token(acc.api_token))
        if not self._tokens:
            raise RuntimeError('no tokens in the database')

    def get_communities(self, ids):
        if len(ids) > COMMUNITIES_PER_REQUEST:
            raise ValueError('too many ids = {0} (max=500)'.format(len(ids)))

        with self._lock:
            token = min(self._tokens, key=lambda t: t.last_used)
            elapsed = (timezone.now() - token.last_used).total_seconds()
            delay = max(0, REQUEST_DELAY_PER_TOKEN - elapsed)
            token.last_used = timezone.now() + TimeDelta(seconds=delay)
        time.sleep(delay)

        response = self._request(
            'groups.getById',
            group_ids=','.join(str(id_) for id_ in ids),
            fields='type,is_closed,verified,age_limits,name,description,members_count,status',
            access_token=token.key,
            v='5.74')
        communities = response.get('response')

        if communities is None:
            err = VkApiResponseError.from_response(response)
            logger.warning('%s with the token %s', repr(err), token.key)
            raise TryAgain()

        return communities

    def get_community_wall(self, id_):
        with self._lock:
            token = min(self._tokens, key=lambda t: t.last_used_for_wall)
            elapsed = (timezone.now() - token.last_used_for_wall).total_seconds()
            delay = max(0, REQUEST_DELAY_PER_TOKEN_FOR_WALL - REQUEST_DELAY_PER_TOKEN - elapsed)
            token.last_used_for_wall = timezone.now() + TimeDelta(seconds=delay)
        time.sleep(delay)
        with self._lock:
            token.last_used = timezone.now() + TimeDelta(seconds=REQUEST_DELAY_PER_TOKEN)
        time.sleep(REQUEST_DELAY_PER_TOKEN)

        response = self._request(
            'wall.get',
            owner_id='-{}'.format(id_),
            offset='0',
            count='100',
            filter='all',
            access_token=token.key,
            v='5.74')
        results = response.get('response')

        if results is None:
            err = VkApiResponseError.from_response(response)
            logger.warning('%s (community=%s, token=%s)', repr(err), id_, token.key)
            if err.code == 15:  # a closed group
                return None
            raise TryAgain()

        posts = results['items']
        if not posts:
            logger.warning('got an empty wall for the community=%s', id_)
        return posts

    def _request(self, method, **params):
        params = urlencode(params)
        params = params.encode('ascii')
        try:
            resp = urlopen('https://api.vk.com/method/' + method, data=params, timeout=HTTP_REQUEST_TIMEOUT)
            data = resp.read()
            with self._lock:
                self._last_successful_request = timezone.now()
                self._network_errors_count = 0
            return json.loads(data)
        except URLError as err:
            with self._lock:
                logger.warning(repr(err))
                duration = (timezone.now() - self._last_successful_request).total_seconds()
                self._network_errors_count += 1
                if self._network_errors_count >= MIN_NETWORK_ERRORS_BEFORE_ALARM and \
                        duration >= MIN_NETWORK_ERRORS_DURATION_BEFORE_ALARM:
                    logger.error(
                        '%s network errors since %s',
                        self._network_errors_count,
                        self._last_successful_request.strftime('%y-%m-%d %H:%M:%S'))
                    self._last_successful_request = timezone.now()
                    self._network_errors_count = 0
            raise TryAgain()
