# -*- coding: utf-8 -*-
import datetime

from Interface import AbstractEventSource
from core.EventBus import EventObject


class EventSource(AbstractEventSource):
    def __init__(self):
        from core.Environment import Environment
        env = Environment.get_instance()
        assert isinstance(env, Environment)
        self._env = env

        # private

        # register funcs
        env.event_bus.add_listener(EVENT.POST_UNIVERSE_CHANGED, self._on_universe_changed)

    def _on_universe_changed(self, event):
        self._universe_changed = True

    def _get_universe(self):
        universe = self._env.get_universe()
        if len(universe) == 0 and DefaultAccountType.STOCK.name not in self._config.base.accounts:
            raise RuntimeError("Current universe is empty. Please use subscribe function before trade")
        return universe

    # [BEGIN] minute event helper
    @staticmethod
    def _get_stock_trading_minutes(trading_date: datetime.date):
        trading_minutes = set()
        current_dt = datetime.datetime.combine(trading_date, datetime.time(9, 31))
        am_end_dt = current_dt.replace(hour=11, minute=30)
        pm_start_dt = current_dt.replace(hour=13, minute=1)
        pm_end_dt = current_dt.replace(hour=15, minute=0)
        while current_dt <= am_end_dt:
            trading_minutes.add(current_dt)
            current_dt += datetime.timedelta(minutes=1)

        current_dt = pm_start_dt
        while current_dt <= pm_end_dt:
            trading_minutes.add(current_dt)
            current_dt += datetime.timedelta(minutes=1)
        return trading_minutes

    def _get_future_trading_minutes(self, trading_date: datetime.date):
        from core.Environment import Environment
        from utils.Functions import convert_int_to_datetime
        trading_minutes = set()
        universe = self._get_universe()
        env = Environment.get_instance()
        for order_book_id in universe:
            if env.get_account_type(order_book_id) == DefaultAccountType.STOCK.name:
                continue
            trading_minutes.update(self._env.data_proxy.get_trading_minutes_for(order_book_id, trading_date))
        return set([convert_int_to_datetime(minute) for minute in trading_minutes])

    def _get_trading_minutes(self, trading_date: datetime.date):
        trading_minutes = set()
        for account_type in self._config.base.accounts:
            if account_type == DefaultAccountType.STOCK.name:
                trading_minutes = trading_minutes.union(self._get_stock_trading_minutes(trading_date))
            elif account_type == DefaultAccountType.FUTURE.name:
                trading_minutes = trading_minutes.union(self._get_future_trading_minutes(trading_date))
        return sorted(list(trading_minutes))
    # [END] minute event helper

    def events(self, start_date: datetime.date, end_date: datetime.date, frequency: str):
        if frequency == "1d":
            # 根据起始日期和结束日期，获取所有的交易日，然后再循环获取每一个交易日
            for day in self._env.data_proxy.get_trading_dates(start_date, end_date):
                date = day.to_pydatetime()
                dt_before_trading = date.replace(hour=0, minute=0)
                dt_bar = date.replace(hour=15, minute=0)
                dt_after_trading = date.replace(hour=15, minute=30)
                dt_settlement = date.replace(hour=17, minute=0)
                yield EventObject(EVENT.BEFORE_TRADING, calendar_dt=dt_before_trading, trading_dt=dt_before_trading)
                yield EventObject(EVENT.BAR, calendar_dt=dt_bar, trading_dt=dt_bar)

                yield EventObject(EVENT.AFTER_TRADING, calendar_dt=dt_after_trading, trading_dt=dt_after_trading)
                yield EventObject(EVENT.SETTLEMENT, calendar_dt=dt_settlement, trading_dt=dt_settlement)
        elif frequency == '1m':
            for day in self._env.data_proxy.get_trading_dates(start_date, end_date):
                before_trading_flag = True
                date = day.to_pydatetime()
                last_dt = None
                done = False

                dt_before_day_trading = date.replace(hour=8, minute=30)
                while True:
                    if done:
                        break
                    exit_loop = True
                    trading_minutes = self._get_trading_minutes(date)
                    for calendar_dt in trading_minutes:
                        if last_dt is not None and calendar_dt < last_dt:
                            continue

                        if calendar_dt < dt_before_day_trading:
                            trading_dt = calendar_dt.replace(
                                year=date.year, month=date.month, day=date.day
                            )
                        else:
                            trading_dt = calendar_dt
                        if before_trading_flag:
                            before_trading_flag = False
                            yield EventObject(EVENT.BEFORE_TRADING,
                                              calendar_dt=calendar_dt - datetime.timedelta(minutes=30),
                                              trading_dt=trading_dt - datetime.timedelta(minutes=30))
                        if self._universe_changed:
                            self._universe_changed = False
                            last_dt = calendar_dt
                            exit_loop = False
                            break
                        # yield handle bar
                        yield EventObject(EVENT.BAR, calendar_dt=calendar_dt, trading_dt=trading_dt)
                    if exit_loop:
                        done = True

                dt = date.replace(hour=15, minute=30)
                yield EventObject(EVENT.AFTER_TRADING, calendar_dt=dt, trading_dt=dt)

                dt = date.replace(hour=17, minute=0)
                yield EventObject(EVENT.SETTLEMENT, calendar_dt=dt, trading_dt=dt)
        elif frequency == "tick":
            data_proxy = self._env.data_proxy
            for day in data_proxy.get_trading_dates(start_date, end_date):
                date = day.to_pydatetime()
                last_tick = None
                last_dt = None
                dt_before_day_trading = date.replace(hour=8, minute=30)
                while True:
                    for tick in data_proxy.get_merge_ticks(self._get_universe(), date, last_dt):
                        # find before trading time
                        if last_tick is None:
                            last_tick = tick
                            dt = tick.datetime
                            before_trading_dt = dt - datetime.timedelta(minutes=30)
                            yield EventObject(EVENT.BEFORE_TRADING, calendar_dt=before_trading_dt,
                                              trading_dt=before_trading_dt)

                        dt = tick.datetime

                        if dt < dt_before_day_trading:
                            trading_dt = dt.replace(year=date.year, month=date.month, day=date.day)
                        else:
                            trading_dt = dt

                        yield EventObject(EVENT.TICK, calendar_dt=dt, trading_dt=trading_dt, tick=tick)

                        if self._universe_changed:
                            self._universe_changed = False
                            last_dt = dt
                            break
                    else:
                        break

                dt = date.replace(hour=15, minute=30)
                yield EventObject(EVENT.AFTER_TRADING, calendar_dt=dt, trading_dt=dt)

                dt = date.replace(hour=17, minute=0)
                yield EventObject(EVENT.SETTLEMENT, calendar_dt=dt, trading_dt=dt)
        else:
            raise NotImplementedError("Frequency {} is not support.".format(frequency))
