# -*- coding:utf-8 -*-
from functools import wraps
import time

__author__ = 'q00222219@huawei'


class RetryDecorator(object):
    """Decorator for retrying a function upon suggested exceptions.
    The decorated function is retried for the given number of times, and the
    sleep time between the retries is incremented until max sleep time is
    reached. If the max retry count is set to -1, then the decorated function
    is invoked indefinitely until an exception is thrown, and the caught
    exception is not in the list of suggested exceptions.
    """
    def __init__(self, max_retry_count=0, inc_sleep_time=1,
                 max_sleep_time=15, exceptions=()):
        """Configure the retry object using the input params.
        :param max_retry_count: maximum number of times the given function must
                                be retried when one of the input 'exceptions'
                                is caught.
        :param inc_sleep_time: incremental time in seconds for sleep time
                               between retries.
        :param max_sleep_time: max sleep time in seconds beyond which the sleep
                               time will not be incremented using param
                               inc_sleep_time. On reaching this threshold,
                               max_sleep_time will be used as the sleep time.
        :param exceptions: suggested exceptions for which the function must be
                           retried
        """
        self._max_retry_count = max_retry_count
        self._inc_sleep_time = inc_sleep_time
        self._max_sleep_time = max_sleep_time
        self._exceptions = exceptions
        self._retry_count = 0
        self._sleep_time = 0

    def __call__(self, f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries = self._max_retry_count
            mdelay = 0
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except self._exceptions:
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay += self._inc_sleep_time
                    if mdelay >= self._max_sleep_time:
                        mdelay = self._max_sleep_time

            return f(*args, **kwargs)

        return f_retry  # true decorator
