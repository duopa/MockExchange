# -*- coding: utf-8 -*-
from .Tick import TickObject


DEFAULT_HANDICAP_NUMBER = 5


class Handicap(object):

    def __init__(self):
        self.a_p = [0.0 for i in range(DEFAULT_HANDICAP_NUMBER + 1)]
        self.a_v = [0 for i in range(DEFAULT_HANDICAP_NUMBER + 1)]
        self.b_p = [0.0 for i in range(DEFAULT_HANDICAP_NUMBER + 1)]
        self.b_v = [0 for i in range(DEFAULT_HANDICAP_NUMBER + 1)]

    def updateTick(self, tick: TickObject):
        self.a_p[1], self.a_p[2], self.a_p[3], self.a_p[4], self.a_p[5] = \
            tick.a1, tick.a2, tick.a3, tick.a4, tick.a5
        self.b_p[1], self.b_p[2], self.b_p[3], self.b_p[4], self.b_p[5] = \
            tick.b1, tick.b2, tick.b3, tick.b4, tick.b5
        self.a_v[1], self.a_v[2], self.a_v[3], self.a_v[4], self.a_v[5] = \
            tick.a1_v, tick.a2_v, tick.a3_v, tick.a4_v, tick.a5_v
        self.b_v[1], self.b_v[2], self.b_v[3], self.b_v[4], self.b_v[5] = \
            tick.b1_v, tick.b2_v, tick.b3_v, tick.b4_v, tick.b5_v
