# -*- coding: utf-8 -*-
from Interface import AbstractCommission, AbstractTax, AbstractMatcher
from core.structure import *
from utils.Constants import OrderType, OrderSide, MatchingType


class BaseMatcher(AbstractMatcher):
    tradingPeriodDict = dict()        # dict 交易时间字典

    def __init__(self):
        from core.Environment import Environment
        from utils.Logger import get_logger
        self.__logger__ = get_logger(self.__class__.__name__, 'logMatcher')
        env = Environment.get_instance()
        assert isinstance(env, Environment)
        self.event_bus = env.event_bus
        self.__deal_decider__ = env.get_deal_decider()      # 撮合时确定价格和数量

        # 交易费和税费，每个具体的交易所都不相同
        self.__commission_decider__ = AbstractCommission()
        self.__tax_decider__ = AbstractTax()

        # 相关参数，从文件载入
        config = env.config.get('Matching', dict())
        self.__updown_price_limit__ = config.get('updown_price_limit', True)

    def match(self, market, order: OrderObject):
        if isinstance(market, TickObject):
            if order.order_book_id != market.order_book_id:
                self.__logger__.error('matching wrong tick and order')
                return
        elif isinstance(market, BarObject):
            if order.order_book_id != market.order_book_id:
                self.__logger__.error('matching wrong bar and order')
                return
            raise NotImplementedError
        else:
            from utils.Exceptions import ParamTypeError
            raise ParamTypeError('market', 'TickObject/BarObject', market)

    def match(self, open_orders: list):
        price_board = self._env.price_board
        for account, order in open_orders:
            assert isinstance(order, OrderObject)
            order_book_id = order.order_book_id
            instrument = self._env.get_instrument(order_book_id)

            if not is_valid_price(price_board.get_last_price(order_book_id)):
                listed_date = instrument.listed_date.date()
                if listed_date == self._trading_dt.date():
                    msg = "Order Cancelled: current security [{order_book_id}] " \
                          "can not be traded in listed date [{listed_date}]"
                    reason = msg.format(
                        order_book_id=order.order_book_id,
                        listed_date=listed_date,
                    )
                else:
                    reason = "Order Cancelled: current bar [{order_book_id}] miss market data.".format(
                        order_book_id=order.order_book_id)
                order.mark_rejected(reason)
                continue

            deal_price = self.__deal_decider__(order_book_id, order.side)
            if order.type == OrderType.LIMIT:
                if order.side == OrderSide.BUY and order.price < deal_price:
                    continue
                if order.side == OrderSide.SELL and order.price > deal_price:
                    continue
                # 是否限制涨跌停不成交
                if self.__updown_price_limit__:
                    if order.side == OrderSide.BUY and deal_price >= price_board.get_limit_up(order_book_id):
                        continue
                    if order.side == OrderSide.SELL and deal_price <= price_board.get_limit_down(order_book_id):
                        continue
                if self.__liquidity_limit__:
                    if order.side == OrderSide.BUY and price_board.get_a1(order_book_id) == 0:
                        continue
                    if order.side == OrderSide.SELL and price_board.get_b1(order_book_id) == 0:
                        continue
            else:
                if self.__updown_price_limit__:
                    if order.side == OrderSide.BUY and deal_price >= price_board.get_limit_up(order_book_id):
                        reason = "Order Cancelled: current bar [{order_book_id}] reach the limit_up price.".format(
                            order_book_id=order.order_book_id)
                        order.mark_rejected(reason)
                        continue
                    if order.side == OrderSide.SELL and deal_price <= price_board.get_limit_down(order_book_id):
                        reason = "Order Cancelled: current bar [{order_book_id}] reach the limit_down price.".format(
                            order_book_id=order.order_book_id)
                        order.mark_rejected(reason)
                        continue
                if self.__liquidity_limit__:
                    if order.side == OrderSide.BUY and price_board.get_a1(order_book_id) == 0:
                        reason = "Order Cancelled: [{order_book_id}] has no liquidity.".format(
                            order_book_id=order.order_book_id)
                        order.mark_rejected(reason)
                        continue
                    if order.side == OrderSide.SELL and price_board.get_b1(order_book_id) == 0:
                        reason = "Order Cancelled: [{order_book_id}] has no liquidity.".format(
                            order_book_id=order.order_book_id)
                        order.mark_rejected(reason)
                        continue

            if self._volume_limit:
                bar = self._env.bar_dict[order_book_id]
                volume_limit = round(bar.volume * self._volume_percent) - self._turnover[order.order_book_id]
                round_lot = instrument.round_lot
                volume_limit = (volume_limit // round_lot) * round_lot
                if volume_limit <= 0:
                    if order.type == OrderType.MARKET:
                        msg = "Order Cancelled: market order {order_book_id} volume {order_volume} due to volume limit"
                        reason = msg.format(
                            order_book_id=order.order_book_id,
                            order_volume=order.quantity
                        )
                        order.mark_cancelled(reason)
                    continue

                unfilled = order.unfilled_quantity
                fill = min(unfilled, volume_limit)
            else:
                fill = order.unfilled_quantity

            ct_amount = account.positions.get_or_create(order.order_book_id).cal_close_today_amount(fill, order.side)
            price = self._slippage_decider.get_trade_price(order.side, deal_price)
            trade = Trade.__from_create__(
                order_id=order.order_id,
                price=price,
                amount=fill,
                side=order.side,
                position_effect=order.position_effect,
                order_book_id=order.order_book_id,
                frozen_price=order.frozen_price,
                close_today_amount=ct_amount
            )
            trade._commission = self.__commission_decider__.get_commission(account.type, trade)
            trade._tax = self.__tax_decider__.get_tax(account.type, trade)
            order.fill(trade)
            self._turnover[order.order_book_id] += fill

            self._env.event_bus.publish_event(EventObject(EVENT.TRADE, account=account, trade=trade, order=order))

            if order.type == OrderType.MARKET and order.unfilled_quantity != 0:
                msg = "Order Cancelled: market order {order_book_id} volume {order_volume} is larger than " \
                      "{volume_percent_limit} percent of current bar volume, fill {filled_volume} actually"
                reason = msg.format(
                    order_book_id=order.order_book_id,
                    order_volume=order.quantity,
                    filled_volume=order.filled_quantity,
                    volume_percent_limit=self._volume_percent * 100.0
                )
                order.mark_cancelled(reason)
