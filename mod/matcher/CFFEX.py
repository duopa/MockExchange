# -*- coding: utf-8 -*-
import datetime

from Interface import AbstractCommission, AbstractTax
from core.structure import *
from utils.Constants import *
from .Base import BaseMatcher


class CFCommission(AbstractCommission):
    """China Future Commission"""
    def __init__(self, multiplier: float, hedge_type: HedgeType=HedgeType.SPECULATION):
        """
        期货目前不计算最小手续费
        """
        self.multiplier = multiplier
        self.hedge_type = hedge_type

    def get_commission(self, trade: TradeObject):
        env = Environment.get_instance()
        assert isinstance(env, Environment)
        info = env.data_proxy.get_commission_info(trade.order_book_id)
        commission = 0
        if info['commission_type'] == CommissionType.BY_MONEY:
            contract_multiplier = env.get_instrument(trade.order_book_id).contract_multiplier
            if trade.position_effect == PositionEffect.OPEN:
                commission += trade.last_price * trade.last_quantity * contract_multiplier * info['open_commission_ratio']
            else:
                commission += trade.last_price * (trade.last_quantity - trade.close_today_amount) * contract_multiplier * info[
                    'close_commission_ratio']
                commission += trade.last_price * trade.close_today_amount * contract_multiplier * info[
                    'close_commission_today_ratio']
        else:
            if trade.position_effect == PositionEffect.OPEN:
                commission += trade.last_quantity * info['open_commission_ratio']
            else:
                commission += (trade.last_quantity - trade.close_today_amount) * info['close_commission_ratio']
                commission += trade.close_today_amount * info['close_commission_today_ratio']
        return commission * self.multiplier


class CFTax(AbstractTax):
    def __init__(self, rate: float=0.0):
        self.rate = rate

    def get_tax(self, trade: TradeObject):
        return 0


INDEX_TIME_PERIOD = [   # 股指期货: 09:30~11:30, 13:00~15:00
    TimeRange(start=datetime.time(hour=9, minute=30), end=datetime.time(hour=11, minute=30)),
    TimeRange(start=datetime.time(hour=13), end=datetime.time(hour=15)),
]


class SSE_SZSE_Matcher(BaseMatcher):
    tradingPeriodDict = {
        'IF': INDEX_TIME_PERIOD, 'IH': INDEX_TIME_PERIOD, 'IC': INDEX_TIME_PERIOD,
    }

    def __init__(self):
        super(SSE_SZSE_Matcher, self).__init__()
        self.__commission_decider__ = CFCommission()
        self.__tax_decider__ = CFTax()
