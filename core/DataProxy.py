# -*- coding: utf-8 -*-
import datetime
import os

import numpy as np
import pandas as pd

from utils import lru_cache


class DataProxy(AbstractDataProxy):
    def __init__(self):
        from core.Environment import Environment

    def __getattr__(self, item):
        return getattr(self._data_source, item)

    def get_trading_calendar(self):
        return self._trading_dates.get_trading_calendar()

    def get_trading_minutes_for(self, order_book_id: str, dt: datetime.datetime):
        instrument = self.instruments(order_book_id)
        minutes = self._data_source.get_trading_minutes_for(instrument, dt)
        return [] if minutes is None else minutes

    def get_yield_curve(self, start_date, end_date, tenor=None):
        if isinstance(tenor, str):
            tenor = [tenor]
        return self._yield_curve.get_yield_curve(start_date, end_date, tenor)

    def get_risk_free_rate(self, start_date, end_date):
        from data.YieldCurve import get_tenor_for
        tenor = get_tenor_for(start_date, end_date)
        yc = self.get_yield_curve(start_date, start_date, [tenor])
        if yc is None or yc.empty:
            return 0
        rate = yc.values[0, 0]
        return 0 if np.isnan(rate) else rate

    def is_suspended(self, order_book_id: str, dt, count=1):
        if count == 1:
            return self._suspend_days.contains(order_book_id, [dt])[0]
        else:
            dates = self.get_n_trading_dates_until(dt, count)
            return self._suspend_days.contains(order_book_id, dates)

    def is_st_stock(self, order_book_id: str, dt, count=1):
        if count == 1:
            return self._st_stock_days.contains(order_book_id, [dt])[0]
        else:
            dates = self.get_n_trading_dates_until(dt, count)
            return self._st_stock_days.contains(order_book_id, dates)

    def get_ex_cum_factor(self, order_book_id: str):
        return self._ex_cum_factor.get_factors(order_book_id)

    def get_split(self, order_book_id: str):
        return self._split_factor.get_factors(order_book_id)

    def get_margin_info(self, id_or_ins):
        from utils.Constants import MarginType

        if isinstance(id_or_ins, str):
            instrument = self.instruments(id_or_ins)
        else:
            instrument = id_or_ins

        return {
            'margin_type': MarginType.BY_MONEY,
            'long_margin_ratio': instrument.margin_rate,
            'short_margin_ratio': instrument.margin_rate,
        }

    def get_commission_info(self, id_or_ins):
        from SecurityInfo import CN_FUTURE_INFO

        if isinstance(id_or_ins, str):
            instrument = self.instruments(id_or_ins)
        else:
            instrument = id_or_ins

        return CN_FUTURE_INFO[instrument.underlying_symbol]['speculation']

    def get_dividend(self, order_book_id: str):
        return self._dividends.get_dividend(order_book_id)

    def get_dividend_by_book_date(self, order_book_id: str, date):
        table = self.get_dividend(order_book_id)

        if table is None or len(table) == 0:
            return None

        dt = date.year * 10000 + date.month * 100 + date.day
        dates = table['book_closure_date']
        pos = dates.searchsorted(dt)

        if pos == len(dates) or dt != dates[pos]:
            return None

        return table[pos]

    def get_split_by_ex_date(self, order_book_id, date):
        from utils.Functions import convert_datetime_date_to_int
        df = self.get_split(order_book_id)
        if df is None or len(df) == 0:
            return

        dt = convert_datetime_date_to_int(date)
        pos = df['ex_date'].searchsorted(dt)
        if pos == len(df) or df['ex_date'][pos] != dt:
            return None

        return df['split_factor'][pos]

    @lru_cache(10240)
    def _get_prev_close(self, order_book_id, dt):
        instrument = self.instruments(order_book_id)
        prev_trading_date = self.get_previous_trading_date(dt)
        bar = self._data_source.history_bars(instrument, 1, '1d', 'close', prev_trading_date,
                                             skip_suspended=False, include_now=False, adjust_orig=dt)
        if bar is None or len(bar) < 1:
            return np.nan
        return bar[0]

    def get_prev_close(self, order_book_id: str, dt: datetime.datetime):
        return self._get_prev_close(order_book_id, dt.replace(hour=0, minute=0, second=0))

    @lru_cache(10240)
    def _get_prev_settlement(self, instrument, dt):
        prev_trading_date = self.get_previous_trading_date(dt)
        bar = self._data_source.history_bars(instrument, 1, '1d', 'settlement', prev_trading_date,
                                             skip_suspended=False, adjust_orig=dt)
        if bar is None or len(bar) == 0:
            return np.nan
        return bar[0]

    def get_prev_settlement(self, order_book_id, dt):
        instrument = self.instruments(order_book_id)
        if instrument.type != 'Future':
            return np.nan
        return self._get_prev_settlement(instrument, dt)

    def get_settle_price(self, order_book_id, date):
        instrument = self.instruments(order_book_id)
        if instrument.type != 'Future':
            return np.nan
        return self._data_source.get_settle_price(instrument, date)

    def get_bar(self, order_book_id, dt, frequency='1d'):
        """convert data from data source to BarObject"""
        instrument = self.instruments(order_book_id)
        if frequency == '1d':
            day_bar = self._data_source.get_bar(instrument, dt, '1d')
            if day_bar:
                return BarObject(instrument, day_bar)
        elif frequency == '1m':
            day_bar, minute_bar = self._data_source.get_bar(instrument, dt, '1m')
            if day_bar:
                return BarObject(instrument, day_bar, m_data=minute_bar)
        else:
            raise ValueError("unknown frequency {}".format(frequency))

    def available_data_range(self, frequency):
        return self._data_source.available_data_range(frequency)

    def get_merge_ticks(self, order_book_id_list, trading_date, last_dt=None):
        raise NotImplementedError

    def non_subscribable(self, order_book_id: str, dt, count=1):
        if count == 1:
            return self._non_subscribable_days.contains(order_book_id, [dt])[0]
        else:
            dates = self.get_n_trading_dates_until(dt, count)
            return self._non_subscribable_days.contains(order_book_id, dates)

    def non_redeemable(self, order_book_id: str, dt, count=1):
        if count == 1:
            return self._non_redeemable_days.contains(order_book_id, [dt])[0]
        else:
            dates = self.get_n_trading_dates_until(dt, count)
            return self._non_redeemable_days.contains(order_book_id, dates)

    def public_fund_commission(self, id_or_ins, buy: bool):
        from SecurityInfo import PUBLIC_FUND_COMMISSION

        if isinstance(id_or_ins, str):
            this_ins = self.instruments(id_or_ins)
        else:
            this_ins = id_or_ins

        if buy:
            return PUBLIC_FUND_COMMISSION[this_ins.fund_type]['Buy']
        else:
            return PUBLIC_FUND_COMMISSION[this_ins.fund_type]['Sell']
