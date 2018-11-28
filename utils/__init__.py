# -*- encoding: UTF-8 -*-
import codecs
import yaml


cached_functions = list()


def lru_cache(*args, **kwargs):
    def decorator(func):
        from functools import lru_cache as origin_lru_cache
        func = origin_lru_cache(*args, **kwargs)(func)
        cached_functions.append(func)
        return func
    return decorator


def load_yaml(path: str):
    """载入yml格式配置文件"""
    with codecs.open(path, encoding='utf-8') as y_f:
        return yaml.load(y_f)


def depreciated_expression(depreciated: str, new: str, version=None):
    if version is None:
        return '[depreciated] expression {} is depreciated and will not work soon, please use {} instead.'.format(
            depreciated, new
        )
    else:
        return "[depreciated] expression {} is depreciated, and will be removed in version {}, please use {} " \
               "instead.".format(depreciated, version, new)


def id_generator(start=1):
    """generate id -> int"""
    i = start
    while True:
        yield i
        i += 1


def property_repr(inst: object):
    "%s(%s)" % (inst.__class__.__name__, __properties_dict__(inst))
    return '{}({})'.format(inst.__class__.__name__, str(__properties_dict__(inst)))


def slots_repr(inst: object):
    return "{}({})".format(inst.__class__.__name__, str(__slots_dict__(inst)))


def dict_repr(inst: object):
    return "{}({})".format(
        inst.__class__.__name__,
        {k: v for k, v in inst.__dict__.items() if k.startswith('_') is False}
    )


def __properties_dict__(inst):
    result = dict()
    for cls in inst.__class__.mro():
        for varname in __iter_properties_of_class__(cls):
            if varname[0] == "_":
                continue
            # FIXME: 这里getattr在iter_properties_of_class中掉用过了，性能比较差，可以优化
            tmp = getattr(inst, varname)
            if varname == "positions":
                tmp = list(tmp.keys())
            if hasattr(tmp, '__simple_object__'):
                result[varname] = tmp.__simple_object__()
            else:
                result[varname] = tmp
    return result


def __slots_dict__(inst):
    result = dict()
    for slot in inst.__slots__:
        result[slot] = getattr(inst, slot)
    return result


def __iter_properties_of_class__(cls):
    for varname in vars(cls):
        value = getattr(cls, varname)
        if isinstance(value, property):
            yield varname
