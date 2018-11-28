# -*- coding: utf-8 -*-

from Interface import AbstractPosition


class BasePosition(AbstractPosition):
    NaN = float('NaN')

    def __init__(self, order_book_id: str):
        self._order_book_id = order_book_id
        self._last_price = self.NaN

    def get_state(self):
        raise NotImplementedError

    def set_state(self, state):
        raise NotImplementedError

    @property
    def order_book_id(self):
        return self._order_book_id

    @property
    def market_value(self):
        """
        [float] 当前仓位市值
        """
        raise NotImplementedError

    @property
    def transaction_cost(self):
        raise NotImplementedError

    @property
    def type(self):
        raise NotImplementedError

    @property
    def last_price(self):
        from core.Environment import Environment
        return (self._last_price if self._last_price == self._last_price else
                Environment.get_instance().get_last_price(self._order_book_id))

    def update_last_price(self):
        from core.Environment import Environment
        price = Environment.get_instance().get_last_price(self._order_book_id)
        if price == price:
            # 过滤掉 nan
            self._last_price = price

    def is_de_listed(self):
        """
        判断合约是否过期
        """
        from core.Environment import Environment
        instrument = Environment.get_instance().get_instrument(self._order_book_id)
        current_date = Environment.get_instance().trading_dt
        if instrument.de_listed_date is not None and current_date >= instrument.de_listed_date:
            return True
        return False

    def apply_settlement(self):
        raise NotImplementedError

    def apply_trade(self, trade):
        raise NotImplementedError
