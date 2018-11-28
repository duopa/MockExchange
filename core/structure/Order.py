# -*- coding: utf-8 -*-
import time

from Interface import AbstractOrderStyle, Persistable, Recordable
from core.structure.Trade import TradeObject
from utils.Constants import *
from utils import property_repr, id_generator

__all__ = [
    'OrderObject',
    'MarketOrder',
    'LimitOrder',
]


class OrderObject(object, Persistable, Recordable):

    order_id_gen = id_generator(int(time.time()))

    __repr__ = property_repr

    def __init__(self, order_book_id: str, quantity: int, order_side: OrderSide, style,
                 offset: OffSet, broker_id: int):
        from utils.Logger import get_logger
        self.__logger__ = get_logger(self.__class__.__name__, 'logOrder')
        self._order_id = next(self.order_id_gen)

        self._broker_id = broker_id
        self._order_book_id = order_book_id
        self._quantity = quantity
        self._side = order_side
        self._offset = offset
        self._status = OrderStatus.PENDING_NEW
        self._filled_quantity = 0
        self._avg_price = 0.0
        self._transaction_cost = 0.0
        if isinstance(style, MarketOrder):
            self._type = OrderType.MARKET
        elif isinstance(style, LimitOrder):
            self._type = OrderType.LIMIT
        else:
            from utils.Exceptions import ParamTypeError
            raise ParamTypeError('style', 'MarketOrder/LimitOrder', style)
        self._frozen_price = style.get_limit_price()

        self._calendar_dt = None
        self._trading_dt = None
        self._message = ''

    def get_state(self, s_type: type):
        if s_type == dict:
            return {
                'order_id': self._order_id,
                'secondary_order_id': self._secondary_order_id,
                'calendar_dt': self._calendar_dt,
                'trading_dt': self._trading_dt,
                'order_book_id': self._order_book_id,
                'quantity': self._quantity,
                'side': self._enum_to_str(self._side),
                'position_effect': self._enum_to_str(self._offset) if self._offset is not None else None,
                'message': self._message,
                'filled_quantity': self._filled_quantity,
                'status': self._enum_to_str(self._status),
                'frozen_price': self._frozen_price,
                'type': self._enum_to_str(self._type),
                'transaction_cost': self._transaction_cost,
                'avg_price': self._avg_price,
            }
        else:
            raise NotImplementedError

    def set_state(self, s_type: type, state):
        if isinstance(state, s_type):
            if isinstance(state, dict):
                d = state
                self._order_id = d['order_id']
                self._calendar_dt = d['calendar_dt']
                self._trading_dt = d['trading_dt']
                self._order_book_id = d['order_book_id']
                self._quantity = d['quantity']
                self._side = self._str_to_enum(OrderSide, d['side'])
                if d['position_effect'] is None:
                    self._offset = None
                else:
                    self._offset = self._str_to_enum(PositionEffect, d['position_effect'])
                self._message = d['message']
                self._filled_quantity = d['filled_quantity']
                self._status = self._str_to_enum(OrderStatus, d['status'])
                self._frozen_price = d['frozen_price']
                self._type = self._str_to_enum(OrderType, d['type'])
                self._transaction_cost = d['transaction_cost']
                self._avg_price = d['avg_price']
        else:
            error_msg = '{}.set_state: type of param state {} does not match param s_type {}'.format(
                self.__class__.__name__, type(state), s_type
            )
            raise TypeError(error_msg)

    @property
    def broker_id(self):
        """int 实例编号"""
        return self._broker_id

    @property
    def order_id(self):
        """
        [int] 唯一标识订单的id
        """
        return self._order_id

    @property
    def trading_datetime(self):
        """
        [datetime.datetime] 订单的交易日期（对应期货夜盘）
        """
        return self._trading_dt

    @property
    def datetime(self):
        """
        [datetime.datetime] 订单创建时间
        """
        return self._calendar_dt

    @property
    def quantity(self):
        """
        [int] 订单数量
        """
        return self._quantity

    @property
    def unfilled_quantity(self):
        """
        [int] 订单未成交数量
        """
        return self._quantity - self._filled_quantity

    @property
    def order_book_id(self):
        """
        [str] 合约代码
        """
        return self._order_book_id

    @property
    def side(self):
        """
        [SIDE] 订单方向
        """
        return self._side

    @property
    def position_effect(self):
        """
        [POSITION_EFFECT] 订单开平（期货专用）
        """
        return self._offset

    @property
    def message(self):
        """
        [str] 信息。比如拒单时候此处会提示拒单原因
        """
        return self._message

    @property
    def filled_quantity(self):
        """
        [int] 订单已成交数量
        """
        return self._filled_quantity

    @property
    def status(self):
        """
        [ORDER_STATUS] 订单状态
        """
        return self._status

    @property
    def price(self):
        """
        [float] 订单价格，只有在订单类型为'限价单'的时候才有意义
        """
        return 0 if self.type == OrderType.MARKET else self._frozen_price

    @property
    def type(self):
        """
        [ORDER_TYPE] 订单类型
        """
        return self._type

    @property
    def avg_price(self):
        """
        [float] 成交均价
        """
        return self._avg_price

    @property
    def transaction_cost(self):
        """
        [float] 费用
        """
        return self._transaction_cost

    @property
    def frozen_price(self):
        """
        [float] 冻结价格
        """
        return self._frozen_price

    def is_final(self):
        return self._status not in {
            OrderStatus.PENDING_NEW,
            OrderStatus.ACTIVE,
            OrderStatus.PENDING_CANCEL
        }

    def is_active(self):
        """
        check whether order is active
        :return: bool
        """
        return self.status == OrderStatus.ACTIVE

    def active(self):
        """
        activate order to make it active
        :return: None
        """
        self._status = OrderStatus.ACTIVE

    def fill(self, trade: TradeObject):
        quantity = trade.last_quantity
        assert self.filled_quantity + quantity <= self.quantity
        new_quantity = self._filled_quantity + quantity
        self._avg_price = (self._avg_price * self._filled_quantity + trade.last_price * quantity) / new_quantity
        self._transaction_cost += trade.commission + trade.tax
        self._filled_quantity = new_quantity
        if self.unfilled_quantity == 0:
            self._status = OrderStatus.FILLED

    def mark_rejected(self, reject_reason: str):
        if not self.is_final():
            self._message = reject_reason
            self._status = OrderStatus.REJECTED
            self.__logger__.debug(reject_reason)

    def mark_cancelled(self, cancelled_reason: str):
        if not self.is_final():
            self._message = cancelled_reason
            self._status = OrderStatus.CANCELLED
            self.__logger__.debug(cancelled_reason)

    def set_frozen_price(self, value):
        assert isinstance(value, (type(None), float))
        self._frozen_price = value

    def __simple_object__(self):
        from utils import __properties_dict__
        return __properties_dict__(self)


class MarketOrder(AbstractOrderStyle):
    __repr__ = OrderType.MARKET.__repr__

    def get_limit_price(self):
        return 0.0


class LimitOrder(AbstractOrderStyle):
    __repr__ = OrderType.LIMIT.__repr__

    def __init__(self, limit_price):
        self.limit_price = float(limit_price)

    def get_limit_price(self):
        return self.limit_price
