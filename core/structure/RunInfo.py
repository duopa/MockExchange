# -*- coding: utf-8 -*-
import datetime

from utils.Constants import *


class RunInfo(object):
    def __init__(self, start_time: datetime.datetime, end_time: datetime.datetime):
        self.universe = set()           # set 涉及的合约
        self.start_time = start_time    # 实例开始时间
        self.end_time = end_time        # 实例结束时间

        self.__market_info_type__ = None
        self.__market_info_seperation__ = None      # 单位毫秒

    def subscribe(self, symbol: str):
        self.universe.add(symbol)

    def set_market_type(self, m_type: MarketInfoType):
        self.__market_info_type__ = m_type

    @property
    def market_info_type(self):
        return self.__market_info_type__

    def set_market_seperation(self, seperation: int):
        self.__market_info_seperation__ = seperation

    @property
    def market_info_seperation(self):
        return self.__market_info_seperation__
