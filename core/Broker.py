# -*- coding: utf-8 -*-
import datetime
import threading

from queue import Queue

from Interface import Persistable, Recordable
from core.structure import *
from core.EventBus import EventObject
from utils import id_generator
from utils.Constants import *


class MockBroker(Persistable, Recordable):
    id_gen = id_generator(1)
    front_datetime = datetime.datetime(year=1970, month=1, day=1, hour=8, minute=0, second=0)
    back_datetime = datetime.datetime(year=2099, month=12, day=31, hour=23, minute=59, second=59)

    def __init__(self, run_info: RunInfo):
        from core.Environment import Environment
        from utils.Logger import get_logger
        env = Environment.get_instance()
        assert isinstance(env, Environment)
        self.__logger__ = get_logger(self.__class__.__name__, 'logMockBroker')
        self.market_source = env.universe
        self.event_bus = env.event_bus

        # public
        self.id = next(self.id_gen)
        if run_info.market_info_type is None:
            self.market_info_type = MarketInfoType(env.config.get('Market', dict()).get('type', 'TICK'))
        else:
            self.market_info_type = run_info.market_info_type
        self.universe = run_info.universe
        self.start_date = run_info.start_time.date()
        self.start_date_time = run_info.start_time.time()
        self.end_date = run_info.end_time.date()
        self.end_date_time = run_info.end_time.time()
        self.open_order_list = list()

        # private
        self.__active__ = False                         # 是否在运行
        self.__market_info_queue_dict__ = dict()        # 数据载入线程暂存队列
        self.__market_info_map__ = dict()               # 最近数据字典
        self.__loading_market_thread_dict__ = dict()

        # init
        for symbol in self.universe:
            self.__market_info_queue_dict__[symbol] = Queue(maxsize=1)

        # prepare market info
        if self.market_info_type == MarketInfoType.TICK:
            for symbol in self.universe:
                new_thread = threading.Thread(
                    target=self.__load_tick__, args=(symbol, ),
                    name='broker {} loading {}'.format(self.id, symbol),
                )
                new_thread.start()
                self.__loading_market_thread_dict__[symbol] = new_thread
        else:
            raise NotImplementedError

        # register
        env.event_bus.add_listener(EVENT.MARKET_CHECK, self.check_market)
        env.event_bus.add_listener(EVENT.MARKET_SEND, self.matching)

    def __load_tick__(self, symbol: str):
        from core.structure import UniverseUnit
        date = self.start_date
        this_universe = self.market_source[symbol]
        assert isinstance(this_universe, UniverseUnit)
        while date <= self.end_date:
            pd_day = this_universe[date.strftime('%Y-%m-%d')]
            for index in pd_day.index:
                new_dict = dict()
                for column in pd_day.column:
                    new_dict[column] = pd_day.loc[column][index]
                new_tick = TickObject(new_dict)
                if self.start_date == new_tick.date and new_tick.time < self.start_date_time:
                    continue
                if self.end_date == new_tick.date and self.end_date_time < new_tick.time:
                    continue
                self.__market_info_queue_dict__[symbol].put(new_tick, block=True, timeout=None)
            date += datetime.timedelta(days=1)

    def check_market(self, event):
        assert isinstance(event, EventObject)
        if self.__active__ is False:
            return
        this_dt, this_symbol, this_market = self.back_datetime, None, None
        for symbol in self.__market_info_map__:
            if self.__market_info_map__[symbol].datetime < this_dt:
                this_market = self.__market_info_map__[symbol]
                this_symbol = symbol
        if this_symbol is None:
            return
        self.event_bus.put(EventObject(
            event_type=EVENT.MARKET_SEND, broker_id=self.id,
            market=this_market))
        if self.__loading_market_thread_dict__[this_symbol].is_alive() \
                or self.__market_info_queue_dict__[this_symbol].full():
            self.__market_info_map__[this_symbol] = self.__market_info_queue_dict__[this_symbol].get(block=True)
        else:
            self.__market_info_map__.pop(this_symbol)

    def start(self):
        # init market info
        for symbol in self.universe:
            if self.__loading_market_thread_dict__[symbol].is_alive() or self.__market_info_queue_dict__[symbol].full():
                self.__market_info_map__[symbol] = self.__market_info_queue_dict__[symbol].get(block=True)

        self.__active__ = True

    def stop(self):
        self.__active__ = False

        for symbol in self.__loading_market_thread_dict__:
            self.__loading_market_thread_dict__[symbol].join()

    # def get_portfolio(self):
    #     return init_portfolio(self._env)

    def get_open_orders(self, order_book_id=None):
        if order_book_id is None:
            return [order for account, order in self.open_order_list]
        else:
            return [order for account, order in self.open_order_list if order.order_book_id == order_book_id]

    # def get_state(self):
    #     return jsonpickle.dumps({
    #         'open_orders': [o.get_state() for account, o in self.open_order_list],
    #         'delayed_orders': [o.get_state() for account, o in self.__delayed_orders__]
    #     }).encode('utf-8')
    #
    # def set_state(self, state: bytes):
    #     self.open_order_list = []
    #     self.__delayed_orders__ = []
    #
    #     value = jsonpickle.loads(state.decode('utf-8'))
    #     for v in value['open_orders']:
    #         o = Order()
    #         o.set_state(v)
    #         account = self._env.get_account(o.order_book_id)
    #         self.open_order_list.append((account, o))
    #     for v in value['delayed_orders']:
    #         o = Order()
    #         o.set_state(v)
    #         account = self._env.get_account(o.order_book_id)
    #         self.__delayed_orders__.append((account, o))

    def update_order(self, order: OrderObject):
        pass

    def matching(self, event: EventObject):
        if getattr(event, 'broker_id', -1) != self.id:
            return

        market = getattr(event, 'market')
        if isinstance(market, TickObject):
            raise NotImplementedError
        elif isinstance(market, BarObject):
            raise NotImplementedError
        else:
            from utils.Exceptions import ParamTypeError
            raise ParamTypeError('event.market', 'TickObject/BarObject', market)

    def _match(self, order_book_id=None):
        if order_book_id is not None:
            open_orders = [(a, o) for (a, o) in self.open_order_list if o.order_book_id == order_book_id]
        else:
            open_orders = self.open_order_list
        self._matcher.match(open_orders)
        final_orders = [(a, o) for a, o in self.open_order_list if o.is_final()]
        self.open_order_list = [(a, o) for a, o in self.open_order_list if not o.is_final()]

        for account, order in final_orders:
            if order.status == OrderStatus.REJECTED or order.status == OrderStatus.CANCELLED:
                self._env.event_bus.publish_event(
                    EventObject(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=order)
                )
