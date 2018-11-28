# -*- coding: utf-8 -*-
import os

from collections import Mapping, Iterable

from Interface import ROOT_PATH
from utils import id_generator
from utils.Persisit import Plist


class MarketDict(Mapping, Iterable):
    id_gen = id_generator(1)

    def __init__(self, data_path: str=os.path.join(ROOT_PATH, 'data', 'temp_market')):
        from utils.Logger import get_logger
        self.__logger__ = get_logger(self.__class__.__name__, 'logMarketDict')
        self.__path__ = data_path

        # check path
        if os.path.exists(data_path) is False:
            os.makedirs(data_path)
        else:
            os.removedirs(data_path)
            os.makedirs(data_path)
        self.__path__ = data_path

        # private
        self.__data__ = dict()
        self.__hist_dict__ = dict()

    def __pjoin__(self, name: str):
        return os.path.join(self.__path__, name)

    def __setitem__(self, key: str, value):
        if self.__data__.__contains__(key):
            if self.__hist_dict__.__contains__(key) is False:
                self.__hist_dict__[key] = Plist(self.__pjoin__(key), keep_history=False)
            self.__hist_dict__[key].append(self.__data__[key])
            self.__data__[key] = value
        else:
            self.__data__[key] = value

    def __getitem__(self, key: str):
        return self.__data__[key]

    def __len__(self):
        return len(self.__data__)

    def __iter__(self):
        return self.__data__.keys()

    def keys(self):
        return self.__data__.keys()

    def values(self):
        return self.__data__.values()

    def items(self):
        return self.__data__.items()

    def snapshot(self, key: str):
        raise NotImplementedError
