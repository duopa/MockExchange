# -*- coding: utf-8 -*-

import jsonpickle

from utils.Constants import DaysCount, DefaultAccountType
from utils import property_repr
from utils.Constants import EVENT


class Portfolio(object):
    __repr__ = property_repr

    def __init__(self, start_date, static_unit_net_value, units, accounts, register_event=True):
        self._start_date = start_date
        self._static_unit_net_value = static_unit_net_value
        self._units = units
        self._accounts = accounts
        self._mixed_positions = None
        if register_event:
            self.register_event()

    def register_event(self):
        from core.Environment import Environment
        event_bus = Environment.get_instance().event_bus
        event_bus.prepend_listener(EVENT.PRE_BEFORE_TRADING, self._pre_before_trading)

    def order(self, order_book_id, quantity, style, target=False):
        from core.Environment import Environment
        account_type = Environment.get_instance().get_account_type(order_book_id)
        return self.accounts[account_type].order(order_book_id, quantity, style, target)

    def get_state(self):
        return jsonpickle.encode({
            'start_date': self._start_date,
            'static_unit_net_value': self._static_unit_net_value,
            'units': self._units,
            'account': {
                name: account.get_state() for name, account in self._accounts.items()
            }
        }).encode('utf-8')

    def set_state(self, state: bytes):
        state = state.decode('utf-8')
        value = jsonpickle.decode(state)
        self._start_date = value['start_date']
        self._static_unit_net_value = value['static_unit_net_value']
        self._units = value['units']
        for k, v in value['account'].items():
            self._accounts[k].set_state(v)

    def _pre_before_trading(self, event):
        self._static_unit_net_value = self.unit_net_value

    @property
    def accounts(self):
        """
        [dict] 账户字典
        """
        return self._accounts

    @property
    def stock_account(self):
        """
        [StockAccount] 股票账户
        """
        return self._accounts.get(DefaultAccountType.STOCK.name, None)

    @property
    def future_account(self):
        """
        [FutureAccount] 期货账户
        """
        return self._accounts.get(DefaultAccountType.FUTURE.name, None)

    @property
    def start_date(self):
        """
        [datetime.datetime] 策略投资组合的开始日期
        """
        return self._start_date

    @property
    def units(self):
        """
        [float] 份额
        """
        return self._units

    @property
    def unit_net_value(self):
        """
        [float] 实时净值
        """
        return self.total_value / self._units

    @property
    def static_unit_net_value(self):
        return self._static_unit_net_value

    @property
    def daily_pnl(self):
        """
        [float] 当日盈亏
        """
        return self.total_value - self._static_unit_net_value * self.units

    @property
    def daily_returns(self):
        """
        [float] 当前最新一天的日收益
        """
        return 0 if self._static_unit_net_value == 0 else self.unit_net_value / self._static_unit_net_value - 1

    @property
    def total_returns(self):
        """
        [float] 累计收益率
        """
        return self.unit_net_value - 1

    @property
    def annualized_returns(self):
        """
        [float] 累计年化收益率
        """
        from core.Environment import Environment
        current_date = Environment.get_instance().trading_dt.date()
        return self.unit_net_value ** (DaysCount.DAYS_A_YEAR / float((current_date - self.start_date).days + 1)) - 1

    @property
    def total_value(self):
        """
        [float]总权益
        """
        return sum(account.total_value for account in self._accounts.items())

    @property
    def portfolio_value(self):
        """
        [Deprecated] 总权益
        """
        return self.total_value

    @property
    def positions(self):
        """
        [dict] 持仓
        """
        if self._mixed_positions is None:
            self._mixed_positions = MixedPositions(self._accounts)
        return self._mixed_positions

    @property
    def cash(self):
        """
        [float] 可用资金
        """
        return sum(account.cash for account in self._accounts.values())

    @property
    def dividend_receivable(self):
        return sum(getattr(account, 'dividend_receivable', 0) for account in self._accounts.values())

    @property
    def transaction_cost(self):
        return sum(account.transaction_cost for account in self._accounts.values())

    @property
    def market_value(self):
        """
        [float] 市值
        """
        return sum(account.market_value for account in self._accounts.values())

    @property
    def pnl(self):
        return (self.unit_net_value - 1) * self.units

    @property
    def starting_cash(self):
        return self.units

    @property
    def frozen_cash(self):
        return sum(account.frozen_cash for account in self._accounts.values())


class MixedPositions(dict):

    def __init__(self, accounts):
        super(MixedPositions, self).__init__()
        self._accounts = accounts

    def __missing__(self, key):
        from core.Environment import Environment
        account_type = Environment.get_instance().get_account_type(key)
        for a_type in self._accounts:
            if a_type == account_type:
                return self._accounts[a_type].positions[key]
        return None

    def __contains__(self, item):
        return item in self.keys()

    def __repr__(self):
        keys = []
        for account in self._accounts.values():
            keys += account.positions.keys()
        return str(sorted(keys))

    def __len__(self):
        return sum(len(account.positions) for account in self._accounts.values())

    def __iter__(self):
        keys = []
        for account in self._accounts.values():
            keys += account.positions.keys()
        for key in sorted(keys):
            yield key

    def items(self):
        items = dict()
        for d in [account.positions.items() for account in self._accounts.values()]:
            items.update(d)
        for k in sorted(items.keys()):
            yield k, items[k]

    def keys(self):
        keys = list()
        for account in self._accounts.values():
            keys += list(account.positions.keys())
        return sorted(keys)
