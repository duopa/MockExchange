# -*- coding: utf-8 -*-
import os

import pandas as pd

from collections import Iterable, Mapping

from Interface import ROOT_PATH


class Universe(Mapping, Iterable):

    def __init__(self, data_path: str=os.path.join(ROOT_PATH, 'data', 'source')):
        from utils.Logger import get_logger
        self.__logger__ = get_logger(self.__class__.__name__, 'logUniverse')

        # check path
        if os.path.exists(data_path) is False:
            os.makedirs(data_path)
        self.__path__ = data_path

    def __list_dir__(self):
        """ list dir names in universe folder, RELEVANT PATH (not abs path)"""
        for item in os.listdir(self.__path__):
            if item.startswith('.'):    # .git or system/IDE support files
                continue
            if item.startswith('$'):    # windows support files
                continue
            if os.path.isdir(os.path.join(self.__path__, item)) is True:
                yield item
            else:
                continue

    def __len__(self):
        return len(list(self.__list_dir__()))

    def __iter__(self):
        return self.__list_dir__()

    def __contains__(self, key: str):
        abs_path = os.path.join(self.__path__, key)
        if os.path.exists(abs_path) is True:
            if os.path.isdir(abs_path) is True:
                return True
            else:
                return False
        else:
            return False

    def __getitem__(self, key: str):
        return UniverseUnit(os.path.join(self.__path__, key))

    def keys(self):
        return self.__list_dir__()

    def values(self):
        self.__logger__.warning('Universe.values decrease efficiency. Please find better solution.')
        for key in self.keys():
            yield self.__getitem__(key)

    def items(self):
        self.__logger__.warning('Universe.items decrease efficiency. Please find better solution.')
        for key in self.keys():
            yield key, self.__getitem__(key)


class UniverseUnit(Mapping, Iterable):

    def __init__(self, data_path: str):
        from utils.Logger import get_logger
        self.__logger__ = get_logger(self.__class__.__name__, 'logUniverse')

        if os.path.exists(data_path) is False:
            error_msg = 'data source path does not exit.'
            self.__logger__.error(error_msg)
            raise FileNotFoundError(error_msg)

        self.__path__ = data_path

    def __list_file__(self):
        for item in os.listdir(self.__path__):
            if item.startswith('.'):    # .git or system/IDE support files
                continue
            if item.startswith('$'):    # windows support files
                continue
            if os.path.isfile(os.path.join(self.__path__, item)) is True:
                yield item
            else:
                continue

    def __len__(self):
        return len(list(self.__list_file__()))

    def __contains__(self, key: str):
        abs_path = os.path.join(self.__path__, key)
        if os.path.exists(abs_path) is True:
            if os.path.isfile(abs_path) is True:
                return True
            else:
                return False
        else:
            return False

    def __iter__(self):
        return self.__list_file__()

    def __getitem__(self, key: str):
        abs_path = os.path.join(self.__path__, key)
        return pd.read_csv(abs_path, encoding='utf-8')

    def keys(self):
        return self.__list_file__()

    def values(self):
        for key in self.keys():
            yield self.__getitem__(key)

    def items(self):
        for key in self.keys():
            yield key, self.__getitem__(key)
