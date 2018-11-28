# -*- coding: utf-8 -*-
import copy
import logging

from collections import OrderedDict


SYSTEM_MOD_LIST = [
    "sys_accounts",
    "sys_analyser",
    "sys_progress",
    "sys_funcat",
    "sys_risk",
    "sys_simulation",
    "sys_stock_realtime",
]


class ModHandler(object):
    def __init__(self):
        self._env = None
        self._mod_list = list()
        self._mod_dict = OrderedDict()

    def set_env(self, env):
        from core.Environment import Environment
        from mod.utils import import_mod
        from utils.Config import AttrDict

        assert isinstance(env, Environment)
        self._env = env
        config = env.config

        for mod_name in config.mod.__dict__:
            mod_config = getattr(config.mod, mod_name)
            if not mod_config.enabled:  # check whether mod is enabled
                continue
            self._mod_list.append((mod_name, mod_config))

        for index, (mod_name, user_mod_config) in enumerate(self._mod_list):
            if hasattr(user_mod_config, 'lib'):  # find mod path
                lib_name = user_mod_config.lib
            elif mod_name in SYSTEM_MOD_LIST:
                lib_name = "mod." + mod_name
            else:
                lib_name = "mod_" + mod_name

            logging.debug("loading mod {}".format(lib_name))  # loading mod
            mod_module = import_mod(lib_name)
            if mod_module is None:
                del self._mod_list[index]
                return
            mod = mod_module.load_mod()

            mod_config = AttrDict(copy.deepcopy(getattr(mod_module, "__config__", {})))
            mod_config.update(user_mod_config)
            setattr(config.mod, mod_name, mod_config)
            self._mod_list[index] = (mod_name, mod_config)
            self._mod_dict[mod_name] = mod

        self._mod_list.sort(key=lambda item: getattr(item[1], "priority", 100))
        env.mod_dict = self._mod_dict

    def start_up(self):
        for mod_name, mod_config in self._mod_list:
            logging.debug("mod start_up [START] {}".format(mod_name))
            self._mod_dict[mod_name].start_up(self._env, mod_config)
            logging.debug("mod start_up [END]   {}".format(mod_name))

    def tear_down(self, *args):
        result = dict()
        for mod_name, __ in reversed(self._mod_list):
            try:
                logging.debug("mod tear_down [START] {}".format(mod_name))
                ret = self._mod_dict[mod_name].tear_down(*args)
                logging.debug("mod tear_down [END]   {}".format(mod_name))
            except Exception as e:
                logging.exception("tear down fail for {}", mod_name)
                continue
            if ret is not None:
                result[mod_name] = ret
        return result


def import_mod(mod_name: str):
    try:
        from importlib import import_module
        return import_module(mod_name)
    except Exception as e:
        logging.error("*" * 30)
        logging.error("Mod Import Error: {}, error: {}", mod_name, e)
        logging.error("*" * 30)
        raise
