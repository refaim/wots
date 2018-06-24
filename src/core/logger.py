import logging
import sys
from multiprocessing import Queue as MpQueue


class WotsLogger(object):
    def __init__(self, name: str, queue: MpQueue):
        logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')
        self.__name = name
        self.__queue = queue

    def get_child(self, name: str) -> 'WotsLogger':
        child_name = name
        if self.__name:
            child_name = '{}.{}'.format(self.__name, child_name)
        return WotsLogger(child_name, self.__queue)

    def __log(self, name, level, message, *args, **kwargs):
        self.__queue.put((name, level, message, args, kwargs))

    def debug(self, message, *args, **kwargs):
        self.__log(self.__name, logging.DEBUG, message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        self.__log(self.__name, logging.INFO, message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        self.__log(self.__name, logging.WARNING, message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self.__log(self.__name, logging.ERROR, message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        self.__log(self.__name, logging.CRITICAL, message, *args, **kwargs)
