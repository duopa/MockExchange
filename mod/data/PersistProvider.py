# -*- coding: utf-8 -*-
import datetime
import hashlib
import pickle
import os

from collections import OrderedDict

from Interface import AbstractStoreProvider, ROOT_PATH
from utils.Constants import PersistMode, EVENT


class BaseStoreProvider(AbstractStoreProvider):
    def __init__(self, path: str=os.path.join('data', 'persist')):
        from utils.Logger import get_logger
        self.__logger__ = get_logger(self.__class__.__name__, 'logStoreProvider')
        self.__path__ = os.path.join(ROOT_PATH, path)
        if os.path.exists(self.__path__) is False:
            os.makedirs(self.__path__)

    def store(self, key: str, value):
        raise NotImplementedError

    def load(self, key: str):
        raise NotImplementedError


class TextStoreProvider(BaseStoreProvider):
    def __init__(self, path: str=os.path.join('data', 'text_persist')):
        super(TextStoreProvider, self).__init__(path)

    def store(self, key: str, value: str):
        with open(os.path.join(self.__path__, key), "w", encoding='utf-8') as f:
            f.write(value)

    def load(self, key: str):
        try:
            with open(os.path.join(self.__path__, key), "r", encoding='utf-8') as f:
                return f.read()
        except IOError:
            return None


class BytesStoreProvider(BaseStoreProvider):
    def __init__(self, path: str=os.path.join('data', 'bytes_persist')):
        super(BytesStoreProvider, self).__init__(path)

    def store(self, key: str, value: bytes):
        # assert isinstance(value, bytes), "value must be bytes"
        with open(os.path.join(self.__path__, key), "wb") as f:
            f.write(value)

    def load(self, key: str, large_file=False):
        try:
            with open(os.path.join(self.__path__, key), "rb") as f:
                return f.read()
        except IOError:
            return None


class ObjectStoreProvider(BaseStoreProvider):
    def __init__(self, path: str=os.path.join('data', 'object_persist')):
        super(ObjectStoreProvider, self).__init__(path)

    def store(self, key: str, value):
        pickle.dump(value, open(os.path.join(self.__path__, key), 'wb'))

    def load(self, key: str):
        try:
            return pickle.load(open(os.path.join(self.__path__, key)), 'rb')
        except IOError:
            return None


class ShelveStoreProvider(BaseStoreProvider):
    def __init__(self, path: str='data', file_name: str=datetime.datetime.now().strftime('%Y%m%d %H%M%S'),
                 new: bool=False):
        from utils.ShelveWrapper import ShelveWrapper
        super(ShelveStoreProvider, self).__init__(path)
        if new is True:
            self.db = ShelveWrapper.init_from(dict(), os.path.join(self.__path__, file_name))
        else:
            self.db = ShelveWrapper(os.path.join(self.__path__, file_name))

    def store(self, key: str, value):
        self.db[key] = value

    def load(self, key: str):
        return self.db.get(key, None)


class CoreObjectsPersistProxy(object):
    def __init__(self, scheduler):
        self._objects = {'scheduler': scheduler}

    def get_state(self):
        import jsonpickle
        result = dict()
        for key, obj in self._objects.items():
            state = obj.get_state()
            if state is not None:
                result[key] = state

        return jsonpickle.dumps(result).encode('utf-8')

    def set_state(self, state: bytes):
        import jsonpickle
        for key, value in jsonpickle.loads(state.decode('utf-8')).items():
            try:
                self._objects[key].set_state(value)
            except KeyError:
                system_log.warn('core object state for {} ignored'.format(key))


class PersistHelper(object):
    def __init__(self, persist_provider, event_bus, persist_mode):
        self._objects = OrderedDict()
        self._last_state = {}
        self._persist_provider = persist_provider
        if persist_mode == PersistMode.REAL_TIME:
            event_bus.add_listener(EVENT.POST_BEFORE_TRADING, self.persist)
            event_bus.add_listener(EVENT.POST_AFTER_TRADING, self.persist)
            event_bus.add_listener(EVENT.POST_BAR, self.persist)
            event_bus.add_listener(EVENT.DO_PERSIST, self.persist)
            event_bus.add_listener(EVENT.POST_SETTLEMENT, self.persist)

    def persist(self, *args):
        for key, obj in self._objects.items():
            try:
                state = obj.get_state()
                if not state:
                    continue
                md5 = hashlib.md5(state).hexdigest()
                if self._last_state.get(key) == md5:
                    continue
                self._persist_provider.store(key, state)
            except Exception as e:
                system_log.exception("PersistHelper.persist fail")
            else:
                self._last_state[key] = md5

    def register(self, key, obj):
        if key in self._objects:
            raise RuntimeError('duplicated persist key found: {}'.format(key))
        self._objects[key] = obj

    def restore(self):
        for key, obj in self._objects.items():
            state = self._persist_provider.load(key)
            system_log.debug('restore {} with state = {}', key, state)
            if not state:
                continue
            obj.set_state(state)


if __name__ == '__main__':
    pass
