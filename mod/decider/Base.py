# -*- coding: utf-8 -*-
from Interface import AbstractDealDecider
from core.structure import OrderObject


class BaseDealDecider(AbstractDealDecider):
    def __init__(self):
        raise NotImplementedError

    def decide_tick(self, tick, order: OrderObject, **kwargs):
        raise NotImplementedError
