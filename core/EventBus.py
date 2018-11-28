# -*- coding: utf-8 -*-
import time

from queue import Empty

from utils.Constants import EVENT


class EventObject(object):
    """事件对象"""
    def __init__(self, event_type: EVENT, **kwargs):
        # self.__dict__ = kwargs
        self.event_type = event_type  # event_type must after __dict__, otherwise event_type will be wiped
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return 'EventObject' + ' '.join('{}:{}'.format(k, v) for k, v in self.__dict__.items())


class EventBus(object):
    """
    事件驱动队列中心

    在事件发生之前注册好所有的事件处理方案(FunctionType)，当发布事件时会运行相应事件类型的处理方案
    """
    def __init__(self):
        from collections import defaultdict
        from queue import Queue
        from threading import Thread
        from utils.Logger import get_logger

        self.__queue__ = Queue()        # 事件队列
        self.__active_status__ = False  # 事件引擎开关
        # 事件处理线程
        self.__thread__ = Thread(target=self.__run__, name='{} event process thread.'.format(self.__class__.__name__))
        self.__handlers__ = defaultdict(list)   # 处理预案队列

        # 计时器，用于触发计时器事件
        self.__timer_sys_thread__ = Thread(
            target=self.__timer_sys__,
            name='{} timer thread.'.format(self.__class__.__name__)
        )
        self.__timer_sys_sleep__ = 1.0  # 计时器触发间隔（默认1秒）

        # 检查并发送行情
        self.__timer_market_thread__ = Thread(
            target=self.__timer_market__,
            name='{} timer market thread'.format(self.__class__.__name__),
        )
        self.__timer_market_sleep__ = 0.1

        self.__logger__ = get_logger(self.__class__.__name__, 'EventEngine')

    def __run__(self):
        while self.__active_status__ is True:
            try:
                event = self.__queue__.get(block=True, timeout=1)
                assert isinstance(event, EventObject)
                for func in self.__handlers__[event.event_type]:
                    # 如果返回 True ，那么消息不再传递下去
                    if func(event) is True:
                        return
            except Empty:
                pass

    def __timer_sys__(self):
        while self.__active_status__ is True:
            self.put(EventObject(event_type=EVENT.SYS_TIMER))
            time.sleep(self.__timer_sys_sleep__)

    def __timer_market__(self):
        while self.__active_status__ is True:
            self.put(EventObject(event_type=EVENT.MARKET_CHECK))
            time.sleep(self.__timer_market_sleep__)

    def add_listener(self, event: EVENT, listener):
        """在事件队列后添加处理方案"""
        self.__handlers__[event].append(listener)

    def prepend_listener(self, event: EVENT, listener):
        """在事件队列前添加处理方案"""
        self.__handlers__[event].insert(0, listener)

    def start(self, timer_sys: int=1000, timer_market: int=100):
        """
        引擎启动
        timer：是否要启动计时器
        :return: None
        """
        # 启动事件处理线程 将引擎设为启动
        self.__active_status__ = True
        self.__thread__.start()

        # 启动计时器，计时器事件间隔默认设定为1秒
        assert timer_sys > 0
        self.__timer_sys_sleep__ = timer_sys * 1000
        self.__timer_sys_thread__.start()

        # 启动行情发送
        assert timer_market > 0
        self.__timer_market_sleep__ = timer_market * 1000
        self.__timer_market_thread__.start()

    def stop(self):
        """停止引擎"""
        # 将引擎设为停止
        self.__active_status__ = False

        # 停止
        self.__timer_sys_thread__.join()
        self.__timer_market_thread__.join()

        # 等待事件处理线程退出
        self.__thread__.join()

    def put(self, event: EventObject):
        self.__queue__.put(event)
