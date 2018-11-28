# -*- coding: utf-8 -*-
import os

from abc import abstractmethod, ABCMeta

from core.structure import *


# 版本号
version = '0.0.1'

# str 根目录
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))


class AbstractCommission:
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_commission(self, trade: TradeObject):
        raise NotImplemented


class AbstractTax:
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_tax(self, trade: TradeObject):
        raise NotImplemented


class AbstractDealDecider:
    __metaclass__ = ABCMeta

    @abstractmethod
    def decide_tick(self, tick: TickObject, order: OrderObject, **kwargs):
        raise NotImplemented

    @abstractmethod
    def decide_bar(self, bar: BarObject, order: OrderObject, **kwargs):
        raise NotImplemented


class AbstractMatcher:
    __metaclass__ = ABCMeta

    @abstractmethod
    def match(self, market, order: OrderObject):
        """match trade -> TradeObject"""
        assert isinstance(market, (TickObject, BarObject))
        raise NotImplemented


class AbstractEventSource:
    """
    事件源接口。LiQuant 从此对象中获取事件，驱动整个事件循环。

    在扩展模块中，可以通过调用 ``env.set_event_source`` 来替换默认的事件源。
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def events(self, start_date, end_date, frequency):
        """
        [Required]

        扩展 EventSource 必须实现 events 函数。

        events 是一个 event generator, 在相应事件的时候需要以如下格式来传递事件

        .. code-block:: python

            yield trading_datetime, calendar_datetime, EventEnum

        其中 trading_datetime 为基于交易日的 datetime, calendar_datetime 为基于自然日的 datetime (因为夜盘的存在，交易日和自然日未必相同)

        EventEnum 为 :class:`~Events`

        :param datetime.date start_date: 起始日期
        :param datetime.date end_date: 结束日期
        :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期

        :return: None
        """
        raise NotImplemented


class AbstractDataSource(object):
    """
    在扩展模块中，可以通过调用 ``env.set_data_source`` 来替换默认的数据源。可参考 :class:`BaseDataSource`。
    """

    def get_bar(self, instrument, dt, frequency):
        """
        根据 dt 来获取对应的 Bar 数据

        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

        :param datetime.datetime dt: calendar_datetime

        :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期

        :return: `numpy.ndarray` | `dict`
        """
        raise NotImplemented

    def get_settle_price(self, instrument, date):
        """
        获取期货品种在 date 的结算价

        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

        :param datetime.date date: 结算日期

        :return: `str`
        """
        raise NotImplemented

    def history_bars(self, instrument, bar_count, frequency, fields, dt, skip_suspended=True,
                     include_now=False, adjust_type='pre', adjust_orig=None):
        """
        获取历史数据

        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

        :param int bar_count: 获取的历史数据数量
        :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期
        :param str fields: 返回数据字段

        =========================   ===================================================
        fields                      字段名
        =========================   ===================================================
        datetime                    时间戳
        open                        开盘价
        high                        最高价
        low                         最低价
        close                       收盘价
        volume                      成交量
        total_turnover              成交额
        datetime                    int类型时间戳
        open_interest               持仓量（期货专用）
        basis_spread                期现差（股指期货专用）
        settlement                  结算价（期货日线专用）
        prev_settlement             结算价（期货日线专用）
        =========================   ===================================================

        :param datetime.datetime dt: 时间
        :param bool skip_suspended: 是否跳过停牌日
        :param bool include_now: 是否包含当天最新数据
        :param str adjust_type: 复权类型，'pre', 'none', 'post'
        :param datetime.datetime adjust_orig: 复权起点；

        :return: `numpy.ndarray`

        """
        raise NotImplemented

    def current_snapshot(self, instrument, frequency, dt):
        """
        获得当前市场快照数据。只能在日内交易阶段调用，获取当日调用时点的市场快照数据。
        市场快照数据记录了每日从开盘到当前的数据信息，可以理解为一个动态的day bar数据。
        在目前分钟回测中，快照数据为当日所有分钟线累积而成，一般情况下，最后一个分钟线获取到的快照数据应当与当日的日线行情保持一致。
        需要注意，在实盘模拟中，该函数返回的是调用当时的市场快照情况，所以在同一个handle_bar中不同时点调用可能返回的数据不同。
        如果当日截止到调用时候对应股票没有任何成交，那么snapshot中的close, high, low, last几个价格水平都将以0表示。

        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

        :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期
        :param datetime.datetime dt: 时间

        :return: :class:`~Snapshot`
        """
        raise NotImplemented

    def get_trading_minutes_for(self, instrument, trading_dt):
        """
        获取证券某天的交易时段，用于期货回测

        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

        :param datetime.datetime trading_dt: 交易日。注意期货夜盘所属交易日规则。

        :return: list[`datetime.datetime`]
        """
        raise NotImplemented

    def available_data_range(self, frequency):
        """
        此数据源能提供数据的时间范围

        :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期

        :return: (earliest, latest)
        """
        raise NotImplemented


class AbstractDataProxy(object):
    """
    数据获取接口。LiQuant 中通过 :class:`DataProxy` 进一步进行了封装，向上层提供更易用的接口。
    """

    def get_trading_calendar(self):
        """
        获取交易日历

        :return: list[:class:`pandas.Timestamp`]
        """
        raise NotImplemented

    # def get_all_instruments(self):
    #     """
    #     获取所有Instrument。
    #
    #     :return: list[:class:`~Instrument`]
    #     """
    #     raise NotImplemented

    def get_yield_curve(self, start_date, end_date, tenor=None):
        """
        获取国债利率

        :param pandas.Timestamp datetime.datetime start_date: 开始日期
        :param pandas.Timestamp datetime.datetime end_date: 结束日期
        :param list str tenor: 利率期限

        :return: pandas.DataFrame, [start_date, end_date]
        """
        raise NotImplemented

    def get_risk_free_rate(self, start_date, end_date):
        """

        :param pandas.Timestamp datetime.datetime start_date: 开始日期
        :param pandas.Timestamp datetime.datetime end_date: 结束日期
        :return: int np.nan
        """
        raise NotImplemented

    def get_split(self, order_book_id):
        """
        获取拆股信息

        :param str order_book_id: 合约名

        :return: `pandas.DataFrame`
        """
        raise NotImplemented

    def get_margin_info(self, id_or_ins):
        """
        获取合约的保证金数据

        :param id_or_ins: str :class:`~Instrument`  合约对象
        :return: dict
        """
        raise NotImplemented

    def get_commission_info(self, id_or_ins):
        """
        获取合约的手续费信息
        :param id_or_ins: str :class:`~Instrument`  合约对象
        :return:
        """
        raise NotImplemented

    def get_dividend(self, order_book_id):
        """
        获取股票/基金分红信息

        :param str order_book_id: 合约名
        :return: `pandas.DataFrame`
        """
        raise NotImplemented

    def get_merge_ticks(self, order_book_id_list, trading_date, last_dt=None):
        """
        获取合并的 ticks

        :param list order_book_id_list: 合约名列表
        :param datetime.date trading_date: 交易日
        :param datetime.datetime last_dt: 仅返回 last_dt 之后的时间

        :return: Tick
        """
        raise NotImplemented


class AbstractOrderStyle:
    __metaclass__ = ABCMeta

    def get_limit_price(self):
        raise NotImplementedError


class AbstractStoreProvider:
    """持久化服务提供者接口。"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def store(self, key: str, value):
        """
        :param str key:
        :param value:
        :return:
        """
        raise NotImplemented

    @abstractmethod
    def load(self, key: str):
        """
        :param str key:
        :return: bytes 如果没有对应的值，返回 None
        """
        raise NotImplemented


class AbstractRecordProvider:
    """记录服务提供者接口"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def record(self, value):
        """
        :param value: list of str / dict
        :return: None
        """
        raise NotImplemented


class Persistable:
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_state(self, s_type: type):
        """
        :param s_type: type
        :return: s_type
        """
        raise NotImplemented

    @abstractmethod
    def set_state(self, s_type: type, state):
        """
        :param s_type: type
        :param state: object
        :return: None
        """
        raise NotImplemented

    @classmethod
    def __subclasshook__(cls, c):
        if cls is Persistable:
            if (any("get_state" in B.__dict__ for B in c.__mro__) and
                    any("set_state" in B.__dict__ for B in c.__mro__)):
                return True
        return NotImplemented


class Recordable:
    __metaclass__ = ABCMeta

    @abstractmethod
    def record_state(self):
        """
        :return: list of str / dict
        """
        raise NotImplemented


class AbstractFrontendValidator:
    __metaclass__ = ABCMeta

    @abstractmethod
    def can_submit_order(self, account, order):
        # FIXME: need a better name
        raise NotImplemented

    @abstractmethod
    def can_cancel_order(self, account, order):
        # FIXME: need a better name
        raise NotImplemented
