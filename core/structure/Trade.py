# -*- coding: utf-8 -*-
import datetime
import time

from utils import property_repr, id_generator
from utils.Constants import *


class TradeObject(object):

    __repr__ = property_repr

    trade_id_gen = id_generator(int(time.time()))

    def __init__(self, order_id: int, order_book_id: str,
                 match_dt: datetime.datetime, trade_dt: datetime.datetime,
                 price: float, amount: int, side: OrderSide, offset: OffSet=OffSet.NONE,
                 commission: float=0.0, tax: float=0.0, close_today_amount: int=0, frozen_price: int=0
                 ):
        self._match_dt = match_dt
        self._trading_dt = trade_dt
        self._order_book_id = order_book_id
        self._price = price
        self._amount = amount
        self._order_id = order_id
        self._commission = commission
        self._tax = tax
        self._trade_id = next(self.trade_id_gen)
        self._close_today_amount = close_today_amount
        self._side = side
        self._offset = offset
        self._frozen_price = frozen_price

    @property
    def order_book_id(self):
        return self._order_book_id

    @property
    def trading_datetime(self):
        return self._trading_dt

    @property
    def datetime(self):
        return self._match_dt

    @property
    def order_id(self):
        return self._order_id

    @property
    def last_price(self):
        return self._price

    @property
    def last_quantity(self):
        return self._amount

    @property
    def commission(self):
        return self._commission

    @property
    def tax(self):
        return self._tax

    @property
    def transaction_cost(self):
        return self._tax + self._commission

    @property
    def side(self):
        return self._side

    @property
    def position_effect(self):
        return self._offset

    @property
    def exec_id(self):
        return self._trade_id

    @property
    def frozen_price(self):
        return self._frozen_price

    @property
    def close_today_amount(self):
        return self._close_today_amount

    def __simple_object__(self):
        from utils import __properties_dict__
        return __properties_dict__(self)
