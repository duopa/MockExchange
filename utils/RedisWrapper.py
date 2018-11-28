# -*- coding: utf-8 -*-
from redis import StrictRedis


class RedisWrapper(object):
    def __init__(self):
        from core.Environment import Environment
        env = Environment.get_instance()
        assert isinstance(env, Environment)
        redis_config = env.config.get('Redis', dict())
        self.__db__ = StrictRedis(
            host=redis_config.get('host'), port=redis_config.get('port', 6379),
            db=redis_config.get('db', 0), password=redis_config.get('password', None),
            decode_responses=False, encoding='utf-8'
        )

    def pubsub(self, **kwargs):
        return self.__db__.pubsub(**kwargs)

    # ------------ [dict operation] ------------ #
