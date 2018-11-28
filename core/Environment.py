# -*- coding: utf-8 -*-
import os


class Environment(object):
    """
    变量传递结构，在程序的各个部分之间（特别是文件之间）传递各项参数

    需要注意，在 python 当中，结构化的内容在函数之间是引用传递的，比如 3 是值传递，而 [3,]就可以引用传递
    """
    _env = None

    def __init__(self):
        from Interface import ROOT_PATH
        from core.EventBus import EventBus
        from core.structure import Universe, MarketDict
        from utils import load_yaml
        from utils.Logger import get_logger
        Environment._env = self

        self.__logger__ = get_logger(self.__class__.__name__, 'Environment', console_print=True)

        # public
        self.config = load_yaml(os.path.join(ROOT_PATH, 'Config.yaml'))
        self.event_bus = EventBus()         # 事件驱动中心
        self.universe = Universe()          # 可用合约池（以 data - source 文件夹内内容为准）
        self.market_dict = MarketDict()     # 行情字典，用于快速获取当前行情以及快照

        # private
        self.__data_proxy__ = None          # 数据接口
        self.__data_source__ = None         # 数据来源
        self.__event_source__ = None        # 事件来源
        self.__store_provider__ = None      # 实时数据持久化方案
        self.__deal_decider__ = None        # 确定成交量和成交价的原则

        # initiation
        timer_market_microseconds = self.config.get('Market', dict()).get('microseconds', 100)
        timer_sys_microseconds = self.config.get('Timer', dict()).get('microseconds', 1000)
        self.event_bus.start(timer_sys=timer_sys_microseconds, timer_market=timer_market_microseconds)

    @classmethod
    def get_instance(cls):
        """
        返回已经创建的 Environment 对象
        """
        if Environment._env is None:
            raise RuntimeError("Environment has not been created.")
        return Environment._env

    def check(self):
        """
        检查 Environment 中运行所需要的内容是否设定完毕
        :return: bool
        """
        for item in (
                self.__data_proxy__, self.event_bus,
        ):
            if item is None:
                return False
        return True

    def get_deal_decider(self):
        from Interface import AbstractDealDecider
        assert isinstance(self.__deal_decider__, AbstractDealDecider)
        return self.__deal_decider__

    def set_deal_decider(self, decider):
        from Interface import AbstractDealDecider
        assert isinstance(decider, AbstractDealDecider)
        self.__deal_decider__ = decider

    def get_data_source(self):
        from Interface import AbstractDataSource
        assert isinstance(self.__data_source__, AbstractDataSource)
        return self.__data_source__

    def set_data_source(self, source):
        from Interface import AbstractDataSource
        assert isinstance(source, AbstractDataSource)
        self.__data_source__ = source

    def get_event_source(self):
        from Interface import AbstractEventSource
        assert isinstance(self.__event_source__, AbstractEventSource)
        return self.__event_source__
    
    def set_event_source(self, source):
        from Interface import AbstractEventSource
        assert isinstance(source, AbstractEventSource)
        self.__event_source__ = source

    def get_store_provider(self):
        from Interface import AbstractStoreProvider
        assert isinstance(self.__store_provider__, AbstractStoreProvider)
        return self.__store_provider__

    def set_store_provider(self, provider):
        from Interface import AbstractStoreProvider
        assert isinstance(provider, AbstractStoreProvider)
        self.__store_provider__ = provider

    def get_data_proxy(self):
        from Interface import AbstractDataProxy
        assert isinstance(self.__data_proxy__, AbstractDataProxy)
        return self.__data_proxy__

    def set_data_proxy(self, data_proxy):
        from Interface import AbstractDataProxy
        assert isinstance(data_proxy, AbstractDataProxy)
        self.__data_proxy__ = data_proxy
