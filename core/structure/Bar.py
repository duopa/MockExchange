# -*- coding: utf-8 -*-
import numpy as np

from utils.Constants import BarStatus


NAMES = ['open', 'close', 'low', 'high', 'settlement', 'limit_up', 'limit_down', 'volume', 'total_turnover',
         'discount_rate', 'acc_net_value', 'unit_net_value', 'open_interest',
         'basis_spread', 'prev_settlement', 'datetime']

NANDict = {i: np.nan for i in NAMES}


class BarObject(object):

    def __init__(self, d_data, m_data=None):
        from utils.Logger import get_logger
        self.__logger__ = get_logger(self.__class__.__name__, 'model.Bar')

        self._data = d_data if d_data is not None else NANDict
        self._m_data = m_data
        self._prev_close = None
        self._prev_settlement = None
        self._basis_spread = None
        self._limit_up = None
        self._limit_down = None
        self.__internal_limit_up = None
        self.__internal_limit_down = None

    @property
    def open(self):
        """
        [float] 当日开盘价
        """
        try:
            return self._m_data["open"]
        except TypeError:
            return self._data["open"]

    @property
    def close(self):
        try:
            return self._m_data["close"]
        except TypeError:
            return self._data["close"]

    @property
    def low(self):
        """
        [float] 截止到当前的最低价
        """
        try:
            return self._m_data["low"]
        except TypeError:
            return self._data["low"]

    @property
    def high(self):
        """
        [float] 截止到当前的最高价
        """
        try:
            return self._m_data["high"]
        except TypeError:
            return self._data["high"]

    @property
    def limit_up(self):
        try:
            v = self._data['limit_up']
            return v if v != 0 else np.nan
        except (KeyError, ValueError):
            return np.nan

    @property
    def limit_down(self):
        try:
            v = self._data['limit_down']
            return v if v != 0 else np.nan
        except (KeyError, ValueError):
            return np.nan

    @property
    def prev_close(self):
        from core.Environment import Environment
        try:
            return self._data['prev_close']
        except (ValueError, KeyError):
            pass

        if self._prev_close is None:
            trading_dt = Environment.get_instance().trading_dt
            data_proxy = Environment.get_instance().data_proxy
            self._prev_close = data_proxy.get_prev_close(self._instrument.order_book_id, trading_dt)
        return self._prev_close

    @property
    def _bar_status(self):
        """
        WARNING: 获取 bar_status 比较耗费性能，而且是lazy_compute，因此不要多次调用！！！！
        """
        if self.isnan or np.isnan(self.limit_up):
            return BarStatus.ERROR
        if self.close >= self.limit_up:
            return BarStatus.LIMIT_UP
        if self.close <= self.limit_down:
            return BarStatus.LIMIT_DOWN
        return BarStatus.NORMAL

    @property
    def last(self):
        """
        [float] 当前最新价
        """
        return self.close

    @property
    def volume(self):
        """
        [float] 截止到当前的成交量
        """
        try:
            return self._m_data["volume"]
        except TypeError:
            return self._data["volume"]

    @property
    def total_turnover(self):
        """
        [float] 截止到当前的成交额
        """
        try:
            return self._m_data["total_turnover"]
        except TypeError:
            return self._data['total_turnover']

    @property
    def discount_rate(self):
        try:
            return self._m_data["discount_rate"]
        except TypeError:
            return self._data['discount_rate']

    @property
    def acc_net_value(self):
        try:
            return self._m_data["acc_net_value"]
        except TypeError:
            return self._data['acc_net_value']

    @property
    def unit_net_value(self):
        try:
            return self._m_data["unit_net_value"]
        except TypeError:
            return self._data['unit_net_value']

    INDEX_MAP = {
        'IF': '000300.SH',
        'IH': '000016.SH',
        'IC': '000905.SH',
    }

    @property
    def settlement(self):
        try:
            return self._m_data["settlement"]
        except TypeError:
            return self._data['settlement']

    @property
    def prev_settlement(self):
        """
        [float] 昨日结算价（期货专用）
        """
        from core.Environment import Environment
        try:
            return self._data['prev_settlement']
        except (ValueError, KeyError):
            pass

        if self._prev_settlement is None:
            trading_dt = Environment.get_instance().trading_dt
            data_proxy = Environment.get_instance().data_proxy
            self._prev_settlement = data_proxy.get_prev_settlement(self._instrument.order_book_id, trading_dt)
        return self._prev_settlement

    @property
    def open_interest(self):
        """
        [float] 截止到当前的持仓量（期货专用）
        """
        try:
            return self._m_data["open_interest"]
        except TypeError:
            return self._data['open_interest']

    @property
    def datetime(self):
        from data.Bars import from_day_bar_index, from_minute_bar_index
        if self._dt is not None:
            return self._dt
        try:
            return from_minute_bar_index(self._m_data['index'])
        except TypeError:
            return from_day_bar_index(self._data['index'])

    @property
    def instrument(self):
        return self._instrument

    @property
    def order_book_id(self):
        """
        [str] 交易标的代码
        """
        return self._instrument.order_book_id

    @property
    def symbol(self):
        """
        [str] 合约简称
        """
        return self._instrument.symbol

    @property
    def is_trading(self):
        """
        [datetime.datetime] 时间戳
        """
        try:
            return self._m_data["volume"] > 0
        except TypeError:
            return self._data['volume'] > 0

    @property
    def isnan(self):
        try:
            return np.isnan(self._m_data['close'])
        except TypeError:
            return np.isnan(self._data['close'])

    @property
    def suspended(self):
        from core.Environment import Environment
        if self.isnan:
            return True

        return Environment.get_instance().data_proxy.is_suspended(
            self._instrument.order_book_id, int(self._data['datetime'] // 1000000)
        )

    def mavg(self, intervals, frequency='1d'):
        from core.Environment import Environment
        if frequency == 'day':
            frequency = '1d'
        if frequency == 'minute':
            frequency = '1m'

        # copy form history
        env = Environment.get_instance()
        dt = env.calendar_dt

        if (env.config.base.frequency == '1m' and frequency == '1d') or \
                ExecutionContext.phase() == ExecutionPhase.BEFORE_TRADING:
            # 在分钟回测获取日线数据, 应该推前一天
            dt = env.data_proxy.get_previous_trading_date(env.calendar_dt.date())
        bars = env.data_proxy.fast_history(self._instrument.order_book_id, intervals, frequency, 'close', dt)
        return bars.mean()

    def vwap(self, intervals, frequency='1d'):
        from core.Environment import Environment
        if frequency == 'day':
            frequency = '1d'
        if frequency == 'minute':
            frequency = '1m'

        # copy form history
        env = Environment.get_instance()
        dt = env.calendar_dt

        if (env.config.base.frequency == '1m' and frequency == '1d') or \
                ExecutionContext.phase() == ExecutionPhase.BEFORE_TRADING:
            # 在分钟回测获取日线数据, 应该推前一天
            dt = env.data_proxy.get_previous_trading_date(env.calendar_dt.date())
        bars = env.data_proxy.fast_history(
            self._instrument.order_book_id, intervals, frequency, ['close', 'volume'], dt
        )
        sum_value = bars['volume'].sum()
        if sum_value == 0:
            # 全部停牌
            return 0

        return np.dot(bars['close'], bars['volume']) / sum

    def __repr__(self):
        base = [
            ('symbol', repr(self._instrument.symbol)),
            ('order_book_id', repr(self._instrument.order_book_id)),
            ('datetime', repr(self.datetime)),
        ]

        if self.isnan:
            base.append(('error', repr('DATA UNAVAILABLE')))
            return 'Bar({0})'.format(', '.join('{0}: {1}'.format(k, v) for k, v in base) + ' NaN BAR')

        if isinstance(self._data, dict):
            # in pt
            base.extend((k, v) for k, v in self._data.items() if k != 'datetime')
        else:
            base.extend((n, self._data[n]) for n in self._data.dtype.names if n != 'datetime')
        return "Bar({0})".format(', '.join('{0}: {1}'.format(k, v) for k, v in base))

    def __getitem__(self, key):
        return self.__dict__[key]


class BarMap(object):
    def __init__(self, data_proxy, frequency: str):
        from core.DataProxy import DataProxy
        from utils.Logger import get_logger
        assert isinstance(data_proxy, DataProxy)
        self.__logger__ = get_logger(self.__class__.__name__, 'logBarMap')
        self._dt = None
        self._data_proxy = data_proxy
        self._frequency = frequency
        self._cache = dict()

    def update_dt(self, dt):
        self._dt = dt
        self._cache.clear()

    def items(self):
        from core.Environment import Environment
        return ((o, self.__getitem__(o)) for o in Environment.get_instance().get_universe())

    def keys(self):
        from core.Environment import Environment
        return (o for o in Environment.get_instance().get_universe())

    def values(self):
        from core.Environment import Environment
        return (self.__getitem__(o) for o in Environment.get_instance().get_universe())

    def __contains__(self, o):
        from core.Environment import Environment
        return o in Environment.get_instance().get_universe()

    def __len__(self):
        from core.Environment import Environment
        return len(Environment.get_instance().get_universe())

    def __getitem__(self, key):
        if not isinstance(key, str):
            raise ValueError('invalid key {} (use order_book_id please)'.format(key))

        this_ins = self._data_proxy.instruments(key)
        if this_ins is None:
            raise ValueError('invalid order book id or symbol: {}'.format(key))
        order_book_id = this_ins.order_book_id

        try:
            return self._cache[order_book_id]
        except KeyError:
            try:
                bar = self._data_proxy.get_bar(order_book_id, self._dt, self._frequency)
            except Exception as e:
                self.__logger__.exception(e)
                raise KeyError("id_or_symbols {} does not exist".format(key))
            if bar is None:
                return BarObject(this_ins, NANDict, dt=self._dt)
            else:
                self._cache[order_book_id] = bar
                return bar

    @property
    def dt(self):
        return self._dt

    def __repr__(self):
        keys = list(self.keys())
        s = ', '.join(keys[:10]) + (' ...' if len(keys) > 10 else '')
        return "{}({})".format(type(self).__name__, s)
