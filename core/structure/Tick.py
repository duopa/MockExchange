# -*- coding: utf-8 -*-
import datetime

from Interface import Persistable, Recordable


class TickObject(object, Persistable, Recordable):
    def __init__(self, tick_dict: dict):
        self._tick = tick_dict

    @property
    def order_book_id(self):
        return self._tick['order_book_id']

    @property
    def date(self):
        return datetime.datetime.strptime(self._tick['date'], '%Y%m%d').date()

    @property
    def time(self):
        return datetime.datetime.strptime(self._tick['time'], '%H%M%S.%f').time()

    @property
    def datetime(self):
        return datetime.datetime.strptime(self._tick['date'] + self._tick['time'], '%Y%m%d%H%M%S.%f')

    @property
    def open(self):
        return self._tick['open']

    @property
    def last(self):
        return self._tick['last']

    @property
    def high(self):
        return self._tick['high']

    @property
    def low(self):
        return self._tick['low']

    @property
    def prev_close(self):
        return self._tick['prev_close']

    @property
    def volume(self):
        return self._tick['volume']

    @property
    def total_turnover(self):
        return self._tick['total_turnover']

    @property
    def open_interest(self):
        return self._tick['open_interest']

    @property
    def prev_settlement(self):
        return self._tick['prev_settlement']

    # FIXME: use dynamic creation
    @property
    def b1(self):
        return self._tick['b1']

    @property
    def b2(self):
        return self._tick['b2']

    @property
    def b3(self):
        return self._tick['b3']

    @property
    def b4(self):
        return self._tick['b4']

    @property
    def b5(self):
        return self._tick['b5']

    @property
    def b1_v(self):
        return self._tick['b1_v']

    @property
    def b2_v(self):
        return self._tick['b2_v']

    @property
    def b3_v(self):
        return self._tick['b3_v']

    @property
    def b4_v(self):
        return self._tick['b4_v']

    @property
    def b5_v(self):
        return self._tick['b5_v']

    @property
    def a1(self):
        return self._tick['a1']

    @property
    def a2(self):
        return self._tick['a2']

    @property
    def a3(self):
        return self._tick['a3']

    @property
    def a4(self):
        return self._tick['a4']

    @property
    def a5(self):
        return self._tick['a5']

    @property
    def a1_v(self):
        return self._tick['a1_v']

    @property
    def a2_v(self):
        return self._tick['a2_v']

    @property
    def a3_v(self):
        return self._tick['a3_v']

    @property
    def a4_v(self):
        return self._tick['a4_v']

    @property
    def a5_v(self):
        return self._tick['a5_v']

    @property
    def limit_up(self):
        return self._tick['limit_up']

    @property
    def limit_down(self):
        return self._tick['limit_down']

    def __repr__(self):
        items = list()
        for name in dir(self):
            if name.startswith("_"):
                continue
            else:
                items.append((name, getattr(self, name)))
        return "Tick({0})".format(', '.join('{0}: {1}'.format(k, v) for k, v in items))

    def __getitem__(self, key: str):
        return getattr(self, key)
