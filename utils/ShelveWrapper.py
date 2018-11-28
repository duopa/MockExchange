# -*- encoding: UTF-8 -*-
import shelve

from collections import Mapping


class ShelveWrapper(Mapping):

    def __init__(self, db_path: str, writeback=False):
        from utils.Logger import get_logger
        Mapping.__init__(self)

        self.__logger__ = get_logger(self.__class__.__name__, 'logShelveWrapper')

        if '.' in db_path:
            if db_path.split('.')[-1] == 'db':
                path = db_path
            else:
                path = '.'.join([db_path, 'db'])
        else:
            path = '.'.join([db_path, 'db'])

        self.__path__ = path
        self.__db__ = shelve.open(self.__path__, writeback=writeback, protocol=None)
        self.__closed__ = False   # tag whether db is closed

        self.__logger__.info('Connected to shelve database {}'.format(path))

    @classmethod
    def init_from(cls, data, db_path: str, writeback=False):
        if isinstance(data, Mapping):
            new_db = cls(db_path=db_path, writeback=writeback)
            new_db.clear()
            for k, v in data.items():
                new_db[k] = v
            return new_db
        else:
            from utils.Exceptions import ParamTypeError
            raise ParamTypeError('structure', 'Mapping', data)

    def __iter__(self):
        for key in self.keys():
            yield key

    def __getitem__(self, key: str):
        return self.__db__[key]

    def __setitem__(self, key: str, value):
        self.__db__[key] = value
        self.__closed__ = False

    def __contains__(self, key: str):
        return self.__db__.__contains__(key)

    def __delitem__(self, key):
        del self.__db__[key]
        self.__closed__ = False

    def __len__(self):
        self.__db__.__len__()

    def __del__(self):
        if self.__closed__ is False:
            self.__logger__.warning('shelve database {} auto closed.'.format(self.__path__))
            self.close()
        del self.__db__
        del self.__path__
        del self.__closed__

    def keys(self):
        return self.__db__.keys()

    def values(self):
        return self.__db__.values()

    def items(self):
        return self.__db__.items()

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def flush(self):
        self.__db__.sync()
        self.__closed__ = False

    def clear(self):
        self.__db__.clear()
        self.__logger__.debug('shelve database {} cleared.'.format(self.__path__))

    def close(self):
        self.__db__.close()
        self.__closed__ = True
        self.__logger__.debug('shelve database {} closed.'.format(self.__path__))

    @property
    def is_active(self):
        return not self.__closed__

    def to_list(self):
        return [var for var in self.values()]

    def to_dict(self):
        new_dict = dict()
        for key, value in self.items():
            new_dict[key] = value
        return new_dict
