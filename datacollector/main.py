import logging

import django
django.setup()

from datacollector.vkapi import VkApi
from datacollector.commupdater import CommunitiesUpdater
from datacollector.wallupdater import WallUpdater


def main():
    logger = logging.getLogger('datacollector')
    logger.info('started')
    try:
        va = VkApi()
        cu = CommunitiesUpdater(va)
        wu = WallUpdater(va)
        cu.start()
        wu.start()
    except Exception as err:
        logger.exception(err)


if __name__ == '__main__':
    main()
