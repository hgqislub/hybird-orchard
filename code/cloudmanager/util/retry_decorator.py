# -*- coding:utf-8 -*-

__author__ = 'q00222219@huawei'

import time
import log as logger


class RetryDecorator(object):
    """Decorator for retrying a function upon suggested exceptions.
    The decorated function is retried for the given number of times, and the
    sleep time between the retries is incremented until max sleep time is
    reached. If the max retry count is set to -1, then the decorated function
    is invoked indefinitely until an exception is thrown, and the caught
    exception is not in the list of suggested exceptions.
    """

    def __init__(self, max_retry_count=0, init_sleep_time=1,
                 inc_sleep_time=0, max_sleep_time=60,
                 catch_exceptions=Exception,
                 raise_exception=None):
        """Configure the retry object using the input params.
        :param max_retry_count: maximum number of times the given function must
                                be retried when one of the input 'exceptions'
                                is caught. When set to -1, it will be retried
                                indefinitely until an exception is thrown
                                and the caught exception is not in param
                                exceptions.
        :param inc_sleep_time: incremental time in seconds for sleep time
                               between retries
        :param max_sleep_time: max sleep time in seconds beyond which the sleep
                               time will not be incremented using param
                               inc_sleep_time. On reaching this threshold,
                               max_sleep_time will be used as the sleep time.
        :param exceptions: suggested exceptions for which the function must be
                           retried
        """
        self._max_retry_count = max_retry_count
        self._init_sleep_time = init_sleep_time
        self._inc_sleep_time = inc_sleep_time
        self._max_sleep_time = max_sleep_time
        self._catch_exceptions = catch_exceptions
        self._raise_exception = raise_exception

    def __call__(self, f):
        def f_retry(*args, **kwargs):
            mtries = self._max_retry_count
            retry_time = -1
            while mtries > 0:
                retry_time += 1
                try:
                    return f(*args, **kwargs)
                except self._catch_exceptions as e:
                    logger.error("error: %s" % e.message)
                    sleep_time = self._init_sleep_time + \
                                 retry_time * self._inc_sleep_time
                    if sleep_time > self._max_sleep_time:
                        sleep_time = self._max_sleep_time
                    time.sleep(sleep_time)
                    mtries -= 1

            try:
                return f(*args, **kwargs)
            except self._catch_exceptions:
                if self._raise_exception:
                    raise self._raise_exception
                else:
                    return None

        return f_retry  # true decorator
