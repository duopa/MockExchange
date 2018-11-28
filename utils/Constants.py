# -*- coding: utf-8 -*-
from collections import namedtuple
from enum import Enum


__all__ = [
    'EVENT',
    'Exchange',
    'OrderType',
    'OrderStatus',
    'OrderSide',
    'OffSet',
    'InstrumentType',
    'PersistMode',
    'MarginType',
    'MatchingType',
    'MarketInfoType',
    'CommissionType',
    'HedgeType',
    'Currency',
    'TimeRange',
    'UNDERLYING_SYMBOL_PATTERN',
    'NIGHT_TRADING_NS',
]


class BaseEnum(Enum):
    def __repr__(self):
        return '{}.{}'.format(self.__class__.__name__, self._name_)


class EVENT(BaseEnum):

    # -------- [single run] -------- #
    INST_CONNECT = 'inst_connect'           # 客户连接事件
    INST_SUBSCRIBE = 'inst_subscribe'       # 客户订阅行情事件
    INST_START = 'inst_start'               # 客户实例运行
    INST_STOP = 'inst_stop'                 # 客户实例停止

    # -------- [market] -------- #
    MARKET_CHECK = 'market_check'           # 检查 market info 是否可以发出
    MARKET_SEND = 'market_send'             # market info 发送事件

    # -------- [matching] -------- #
    ORDER = 'order'                         # 订单事件
    TRADE = 'trade'                         # 成交事件

    ON_LINE_PROFILER_RESULT = 'on_line_profiler_result'

    # -------- [store] -------- #
    DO_PERSIST = 'do_persist'               # persist immediately
    DO_RECORD = 'do_record'                 # record immediately

    # -------- [system] -------- #
    SYS_TIMER = 'sys_timer'                 # 计时器事件
    SYS_START = 'sys_start'                 # 系统开始
    SYS_HOLD_SET = 'sys_hold_set'           # 系统暂停
    SYS_HOLD_CANCEL = 'sys_hold_cancel'     # 系统暂停恢复
    SYS_STOP = 'sys_stop'                   # 系统结束
    SYS_UNIVERSE_CHANGE = 'sys_universe_change'  # 策略池变化


class Exchange(BaseEnum):
    SSE = "SSE"                 # 上交所
    SZSE = "SZSE"               # 深交所
    CFFEX = "CFFEX"             # 中金所
    SHFE = "SHFE"               # 上期所
    CZCE = "CZCE"               # 郑商所
    DCE = "DCE"                 # 大商所
    SGE = "SGE"                 # 上金所
    INE = "INE"                 # 上海国际能源交易中心
    HKEX = "HKEX"               # 港交所
    SMART = "SMART"             # IB智能路由（股票、期权）
    NYMEX = "NYMEX"             # IB 期货
    GLOBEX = "GLOBEX"           # CME电子交易平台
    IDEALPRO = "IDEALPRO"       # IB外汇ECN
    OANDA = "OANDA"             # OANDA外汇做市商
    OKCOIN = "OKCOIN"           # OKCOIN比特币交易所


class MarketInfoType(BaseEnum):
    """行情数据类型"""
    TICK = 'TICK'               # 快照数据
    BAR = 'BAR'                 # k线数据


class MatchingType(BaseEnum):
    """撮合方式"""
    CURRENT_BAR_CLOSE = "CURRENT_BAR_CLOSE"
    NEXT_BAR_OPEN = "NEXT_BAR_OPEN"
    NEXT_TICK_LAST = "NEXT_TICK_LAST"
    NEXT_TICK_BEST_OWN = "NEXT_TICK_BEST_OWN"
    NEXT_TICK_BEST_COUNTERPARTY = "NEXT_TICK_BEST_COUNTERPARTY"


class OrderType(BaseEnum):
    """订单类型"""
    MARKET = "MARKET"       # 市价单
    LIMIT = "LIMIT"         # 限价单


class OrderStatus(BaseEnum):
    """订单状态"""
    PENDING_NEW = "PENDING_NEW"         # 新订单
    # PENDING_CANCEL = "PENDING_CANCEL"   # 新订单直接取消
    ACTIVE = "ACTIVE"                   # 活跃订单
    FILLED = "FILLED"                   # 全部成交
    REJECTED = "REJECTED"               # 拒绝订单（失败）
    CANCELLED = "CANCELLED"             # 订单取消


class OrderSide(BaseEnum):
    """订单方向"""
    BUY = "BUY"         # 买
    SELL = "SELL"       # 卖
    RQMC = "RQMC"       # 融券卖出
    RZMR = "RZMR"       # 融资买入


class OffSet(BaseEnum):
    """开平仓方向"""
    NONE = "NONE"       # 无
    OPEN = "OPEN"       # 开仓
    CLOSE = "CLOSE"     # 平仓
    CLOSETODAY = "CLOSETODAY"   # 平今
    CLOSEYESTERDAY = "CLOSEYESTERDAY"  # 平昨


class OptionSide(BaseEnum):
    """期权方向"""
    CALL = "CALL"       # 看涨期权
    PUT = "PUT"         # 看跌期权


class ProductStatus(BaseEnum):
    """合约状态"""
    BeforeTrading = "BeforeTrading"     # 开盘前
    NoTrading = "NoTrading"             # 非交易
    Continues = "Continues"             # 连续交易
    AuctionOrdering = "AuctionOrdering"  # 集合竞价报单
    AuctionBalance = "AuctionBalance"   # 集合竞价价格平衡
    AuctionMatch = "AuctionMatch"       # 集合竞价撮合
    Closed = "Closed"                   # 收盘


class InstrumentType(BaseEnum):
    CS = "CS"                       # 股票
    FUTURE = "FUTURE"               # 期货
    OPTION = "OPTION"               # 期权
    COMBINATION = "COMBINATION"     # 组合
    FOREX = "FOREX"                 # 外汇
    DEFER = "DEFER"                 # 延期
    INDEX = "INDEX"                 # 指数
    # ETF = "ETF"
    # LOF = "LOF"
    # FENJI_MU = "FENJI_MU"
    # FENJI_A = "FENJI_A"
    # FENJI_B = "FENJI_B"
    # PUBLIC_FUND = 'PUBLIC_FUND'


class PersistMode(BaseEnum):
    ON_CRASH = "ON_CRASH"
    REAL_TIME = "REAL_TIME"
    ON_NORMAL_EXIT = "ON_NORMAL_EXIT"


class MarginType(BaseEnum):
    BY_MONEY = "BY_MONEY"
    BY_VOLUME = "BY_VOLUME"


class CommissionType(BaseEnum):
    BY_MONEY = "BY_MONEY"
    BY_VOLUME = "BY_VOLUME"


class HedgeType(BaseEnum):
    HEDGE = "hedge"                     # 对冲
    SPECULATION = "speculation"         # 投机
    ARBITRAGE = "arbitrage"             # 套利


class Currency(BaseEnum):
    CNY = "CNY"     # 人民币
    USD = "USD"     # 美元
    EUR = "EUR"     # 欧元
    HKD = "HKD"     # 港币
    GBP = "GBP"     # 英镑
    JPY = "JPY"     # 日元
    KRW = "KWR"     # 韩元
    CAD = "CAD"     # 加元
    AUD = "AUD"     # 澳元
    CHF = "CHF"     # 瑞郎
    SGD = "SGD"     # 新加坡元
    MYR = "MYR"     # 马拉西亚币
    IDR = "IDR"     # 印尼币
    NZD = "NZD"     # 新西兰币
    VND = "VND"     # 越南盾
    THB = "THB"     # 泰铢
    PHP = "PHP"     # 菲律宾币


TimeRange = namedtuple('TimeRange', ['start', 'end'])

UNDERLYING_SYMBOL_PATTERN = "([a-zA-Z]+)\d+"

NIGHT_TRADING_NS = ["CU", "AL", "ZN", "PB", "SN", "NI", "RB", "HC", "BU", "RU", "AU", "AG", "Y", "M", "A", "B", "P",
                    "J", "JM", "I", "CF", "SR", "OI", "MA", "ZC", "FG", "RM", "CY", "TA"]
