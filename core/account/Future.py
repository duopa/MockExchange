# -*- coding: utf-8 -*-

import six

from model.BaseAccount import BaseAccount
from core.Environment import Environment
from model.Event import EVENT
from utils.Constants import DefaultAccountType, PositionEffect, OrderSide
from utils.Logger import user_system_log

from ..api.api_future import order


def margin_of(order_book_id, quantity, price):
    env = Environment.get_instance()
    margin_info = env.data_proxy.get_margin_info(order_book_id)
    margin_multiplier = env.config.base.margin_multiplier
    margin_rate = margin_info['long_margin_ratio'] * margin_multiplier
    contract_multiplier = env.get_instrument(order_book_id).contract_multiplier
    return quantity * contract_multiplier * price * margin_rate


class FutureAccount(BaseAccount):

    def register_event(self):
        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.SETTLEMENT, self._settlement)
        event_bus.add_listener(EVENT.ORDER_PENDING_NEW, self._on_order_pending_new)
        event_bus.add_listener(EVENT.ORDER_CREATION_REJECT, self._on_order_creation_reject)
        event_bus.add_listener(EVENT.ORDER_CANCELLATION_PASS, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.ORDER_UNSOLICITED_UPDATE, self._on_order_unsolicited_update)
        event_bus.add_listener(EVENT.TRADE, self._on_trade)
        if self.AGGRESSIVE_UPDATE_LAST_PRICE:
            event_bus.add_listener(EVENT.BAR, self._on_bar)
            event_bus.add_listener(EVENT.TICK, self._on_tick)

    def fast_forward(self, orders, trades=list()):
        # 计算 Positions
        for trade in trades:
            if trade.exec_id in self._backward_trade_set:
                continue
            self._apply_trade(trade)
        # 计算 Frozen Cash
        self._frozen_cash = sum(self._frozen_cash_of_order(order) for order in orders if order.is_active())

    def order(self, order_book_id, quantity, style, target=False):
        position = self.positions[order_book_id]
        if target:
            # For order_to
            quantity = quantity - position.buy_quantity + position.sell_quantity
        orders = []
        if quantity > 0:
            # 平昨仓
            if position.sell_old_quantity > 0:
                orders.append(order(
                    order_book_id,
                    min(quantity, position.sell_old_quantity),
                    OrderSide.BUY,
                    PositionEffect.CLOSE,
                    style
                ))
                quantity -= position.sell_old_quantity
            if quantity <= 0:
                return orders
            # 平今仓
            if position.sell_today_quantity > 0:
                orders.append(order(
                    order_book_id,
                    min(quantity, position.sell_today_quantity),
                    OrderSide.BUY,
                    PositionEffect.CLOSE_TODAY,
                    style
                ))
                quantity -= position.sell_today_quantity
            if quantity <= 0:
                return orders
            # 开多仓
            orders.append(order(
                order_book_id,
                quantity,
                OrderSide.BUY,
                PositionEffect.OPEN,
                style
            ))
            return orders
        else:
            # 平昨仓
            quantity *= -1
            if position.buy_old_quantity > 0:
                orders.append(order(
                    order_book_id,
                    min(quantity, position.buy_old_quantity),
                    OrderSide.SELL,
                    PositionEffect.CLOSE,
                    style
                ))
                quantity -= position.buy_old_quantity
            if quantity <= 0:
                return orders
            # 平今仓
            if position.buy_today_quantity > 0:
                orders.append(order(
                    order_book_id,
                    min(quantity, position.buy_today_quantity),
                    OrderSide.SELL,
                    PositionEffect.CLOSE_TODAY,
                    style
                ))
                quantity -= position.buy_today_quantity
            if quantity <= 0:
                return orders
            # 开空仓
            orders.append(order(
                order_book_id,
                quantity,
                OrderSide.SELL,
                PositionEffect.OPEN,
                style
            ))
            return orders

    def get_state(self):
        return {
            'positions': {
                order_book_id: position.get_state()
                for order_book_id, position in six.iteritems(self._positions)
            },
            'frozen_cash': self._frozen_cash,
            'total_cash': self._total_cash,
            'backward_trade_set': list(self._backward_trade_set),
            'transaction_cost': self._transaction_cost,
        }

    def set_state(self, state):
        self._frozen_cash = state['frozen_cash']
        self._backward_trade_set = set(state['backward_trade_set'])
        self._transaction_cost = state['transaction_cost']

        margin_changed = 0
        self._positions.clear()
        for order_book_id, v in six.iteritems(state['positions']):
            position = self._positions.get_or_create(order_book_id)
            position.set_state(v)
            if 'margin_rate' in v and abs(v['margin_rate'] - position.margin_rate) > 1e-6:
                margin_changed += position.margin * (v['margin_rate'] - position.margin_rate) / position.margin_rate

        self._total_cash = state['total_cash'] + margin_changed


    @property
    def type(self):
        return DefaultAccountType.FUTURE.name

    @staticmethod
    def _frozen_cash_of_order(order):
        if order.position_effect == PositionEffect.OPEN:
            return margin_of(order.order_book_id, order.unfilled_quantity, order.frozen_price)
        else:
            return 0

    @staticmethod
    def _frozen_cash_of_trade(trade):
        if trade.position_effect == PositionEffect.OPEN:
            return margin_of(trade.order_book_id, trade.last_quantity, trade.frozen_price)
        else:
            return 0

    @property
    def total_value(self):
        return self._total_cash + self.margin + self.holding_pnl

    # -- Margin 相关
    @property
    def margin(self):
        """
        [float] 总保证金
        """
        return sum(position.margin for position in six.itervalues(self._positions))

    @property
    def buy_margin(self):
        """
        [float] 买方向保证金
        """
        return sum(position.buy_margin for position in six.itervalues(self._positions))

    @property
    def sell_margin(self):
        """
        [float] 卖方向保证金
        """
        return sum(position.sell_margin for position in six.itervalues(self._positions))

    # -- PNL 相关
    @property
    def daily_pnl(self):
        """
        [float] 当日盈亏
        """
        return self.realized_pnl + self.holding_pnl - self.transaction_cost

    @property
    def holding_pnl(self):
        """
        [float] 浮动盈亏
        """
        return sum(position.holding_pnl for position in six.itervalues(self._positions))

    @property
    def realized_pnl(self):
        """
        [float] 平仓盈亏
        """
        return sum(position.realized_pnl for position in six.itervalues(self._positions))

    def _settlement(self, event):
        total_value = self.total_value

        for position in list(self._positions.values()):
            order_book_id = position.order_book_id
            if position.is_de_listed() and position.buy_quantity + position.sell_quantity != 0:
                user_system_log.warn(
                    "{order_book_id} is expired, close all positions by system".format(order_book_id=order_book_id))
                del self._positions[order_book_id]
            elif position.buy_quantity == 0 and position.sell_quantity == 0:
                del self._positions[order_book_id]
            else:
                position.apply_settlement()
        self._total_cash = total_value - self.margin - self.holding_pnl

        # 如果 total_value <= 0 则认为已爆仓，清空仓位，资金归0
        if total_value <= 0:
            self._positions.clear()
            self._total_cash = 0

        self._backward_trade_set.clear()

    def _on_bar(self, event):
        for position in self._positions.values():
            position.update_last_price()

    def _on_tick(self, event):
        for position in self._positions.values():
            position.update_last_price()

    def _on_order_pending_new(self, event):
        if self != event.account:
            return
        self._frozen_cash += self._frozen_cash_of_order(event.order)

    def _on_order_creation_reject(self, event):
        if self != event.account:
            return
        self._frozen_cash -= self._frozen_cash_of_order(event.order)

    def _on_order_unsolicited_update(self, event):
        if self != event.account:
            return
        self._frozen_cash -= self._frozen_cash_of_order(event.order)

    def _on_trade(self, event):
        if self != event.account:
            return
        self._apply_trade(event.trade)

    def _apply_trade(self, trade):
        if trade.exec_id in self._backward_trade_set:
            return
        order_book_id = trade.order_book_id
        position = self._positions.get_or_create(order_book_id)
        delta_cash = position.apply_trade(trade)

        self._transaction_cost += trade.transaction_cost
        self._total_cash -= trade.transaction_cost
        self._total_cash += delta_cash
        self._frozen_cash -= self._frozen_cash_of_trade(trade)
        self._backward_trade_set.add(trade.exec_id)
