"""
.. module:: wellknown
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module that provides a wellknow startup configuration singleton.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import threading

from automojo.xmodules.xcollections.context import Context


# NOTE: This code is loaded super early where there is likely to only be a single thread
#       so there is likely no need for any locking.


CONTEXT_SINGLETON = None

SINGLETON_LOCK = threading.RLock()


def ContextSingleton() -> Context:
    """
        The `ContextSingleton` function returns a singleton instance of the `Context` object.
        This is used to store data that can be shared between processes and systems.

        :return: A singleton instance of the `Context`.
    """

    global CONTEXT_SINGLETON

    SINGLETON_LOCK.acquire()
    try:
        if CONTEXT_SINGLETON is None:
            CONTEXT_SINGLETON = Context()
    finally:
        SINGLETON_LOCK.release()

    return CONTEXT_SINGLETON