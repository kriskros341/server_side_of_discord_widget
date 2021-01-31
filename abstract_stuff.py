from abc import ABCMeta, abstractmethod


class SingletonDecorator(object):
    """
    Newbies love their globals
    I love my fancy globals!
    Note to self: please do not overuse
    """
    def __init__(self, klass):
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = self.klass(*args, **kwargs)
        return self.instance


class AbstractStateObserver(metaclass=ABCMeta):
    @abstractmethod
    def interpret_data(self, msg):
        pass
