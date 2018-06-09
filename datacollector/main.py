import logging

import django
django.setup()

from datacollector.vkapi import VkApi
from datacollector.commupdater import CommunitiesUpdater
from datacollector.wallupdater import WallUpdater


LOGGING_FORMAT = '%(asctime)s %(levelname)-8s %(name)s - %(message)s'


def main():
    logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)
    try:
        va = VkApi()
        cu = CommunitiesUpdater(va)
        wu = WallUpdater(va)
        cu.start()
        wu.start()
    except Exception as err:
        logging.exception(err)


if __name__ == '__main__':
    main()
