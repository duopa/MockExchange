# -*- coding: utf-8 -*-
import datetime

from collections import defaultdict

from Interface import AbstractCommission, AbstractTax
from core.structure import TradeObject
from utils.Constants import *
from .Base import BaseMatcher


class CSCommission(AbstractCommission):
    """China Stock Commission"""
    def __init__(self):
        self.rate = 0.0008
        self.multiplier = 1.0
        self.min_commission = 5
        self.commission_map = defaultdict(lambda: self.min_commission)

    def get_commission(self, trade: TradeObject):
        """
        计算手续费这个逻辑比较复杂，按照如下算法来计算：
        1.  定义一个剩余手续费的概念，根据order_id存储在commission_map中，默认为min_commission
        2.  当trade来时计算该trade产生的手续费cost_money
        3.  如果cost_money > commission
            3.1 如果commission 等于 min_commission，说明这是第一笔trade，此时，直接commission置0，返回cost_money即可
            3.2 如果commission 不等于 min_commission, 则说明这不是第一笔trade,此时，直接cost_money - commission即可
        4.  如果cost_money <= commission
            4.1 如果commission 等于 min_commission, 说明是第一笔trade, 此时，返回min_commission(提前把最小手续费收了)
            4.2 如果commission 不等于 min_commission， 说明不是第一笔trade, 之前的trade中min_commission已经收过了，所以返回0.
        """
        order_id = trade.order_id

        commission = self.commission_map[order_id]
        cost_money = trade.last_price * trade.last_quantity * self.rate * self.multiplier
        if cost_money > commission:
            if commission == self.min_commission:
                self.commission_map[order_id] = 0
                return cost_money
            else:
                self.commission_map[order_id] = 0
                return cost_money - commission
        else:
            if commission == self.min_commission:
                self.commission_map[order_id] -= cost_money
                return commission
            else:
                self.commission_map[order_id] -= cost_money
                return 0


class CSTax(AbstractTax):
    def __init__(self):
        self.rate = 0.001

    def get_tax(self, trade: TradeObject):
        cost_money = trade.last_price * trade.last_quantity
        return cost_money * self.rate if trade.side == OrderSide.SELL else 0


class SSE_SZSE_Matcher(BaseMatcher):
    tradingPeriodDict = {
        None: [  # 股票: 09:30~11:30, 13:00~15:00
            TimeRange(start=datetime.time(hour=9, minute=30), end=datetime.time(hour=11, minute=30)),
            TimeRange(start=datetime.time(hour=13), end=datetime.time(hour=15)),
        ],
    }

    def __init__(self):
        super(SSE_SZSE_Matcher, self).__init__()
        self.__commission_decider__ = CSCommission()
        self.__tax_decider__ = CSTax()
