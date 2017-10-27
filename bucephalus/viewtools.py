import sys
import copy
import logging
import traceback

import ujson
import numpy as np
import pandas as pd


def parse_tags(tags):
    "Parses tags passed un the url arguments"
    ret = {}
    for t in tags:
        item = t.split(':')
        if not len(item) == 2:
            raise RuntimeError('Invalid tag {}'.format(t))
        ret[item[0]] = item[1]
    return ret

def dict_merge_impl(dct, merge_dct):
    "Inner function for recursively merging dicts"
    for k, v in merge_dct.items():
        if (k in dct
                and isinstance(dct[k], dict)
                and isinstance(v, dict)):
            dict_merge_impl(dct[k], v)
        else:
            dct[k] = copy.deepcopy(merge_dct[k])

def dict_merge(dcts):
    "Function for recursively merging dicts"
    if len(dcts) == 1:
        return copy.deepcopy(dcts[0])

    ret = copy.deepcopy(dcts[0])
    for a in dcts[1:]:
        dict_merge_impl(ret, a)

    return ret

def template_recurse(tmpl, tags):
    """
    Recursively applies string templating to a dict or list
    """
    if isinstance(tmpl, str):
        ret = tmpl
        for k, v in tags.items():
            # If the value we are replacing is an exact match for a key, return the value as-is - we're assuming
            # here that we are NOT replacing a substring in a larger string "hello {{name}}", but that the
            # value should be used as-is, i.e. not converted into a string - i.e. it is a KEY in the JSON, not a VALUE.
            if ret == k:
                return v
            # Try to perform a simple string substitution - this assumes that the value is a string, or can be
            # converted to a string without any issues.
            ret = ret.replace(k, str(v))

        return ret

    if isinstance(tmpl, list):
        return [template_recurse(v, tags) for v in tmpl]

    if isinstance(tmpl, dict):
        return {k:template_recurse(v, tags) for k, v in tmpl.items()}

    return tmpl

def encode_series(dates, data):
    ret = pd.Series(np.array(data), dates.astype(int)/1000000)
    return ret.reset_index()

def encode_pandas_series(series):
    try:
        ret = pd.Series(series.values, series.index.astype(int)/1000000)
        return ret.reset_index().values
    except:
        return series.values

def level_value_string_sub(s, lspec):
    ret = s

    for lev, val in lspec.items():
        tmpl = '#%s#'%lev
        if tmpl in ret:
            ret = ret.replace(tmpl, str(val))

    return ret

def freeze_tags(tags):
    return frozenset(sorted(tags.items()))

def unfreeze_tags(frozen_tags):
    return dict(frozen_tags)

def parse_result_series(result):
    """
    Convert db results to a jsonable format
    """
    if isinstance(result, np.ndarray):
        return result

    if result is None or not len(result):
        return None

    dates, values = result
    return pd.DataFrame({0:dates.astype(int)/1000,1:values})

def to_json(obj):
    try:
        if 'data' not in obj:
            return ujson.dumps(obj)

        dfjson = obj['data'].to_json(orient='values')
        obj['data'] = [[[]]]
        objson = ujson.dumps(obj)
        return objson.replace('[[[]]]', dfjson)

    except Exception:
        print(obj)
        msg = build_error_message('There was an error encoding data for view {}:'.format(obj['id']))
        logging.error(msg)
        return ujson.dumps(build_error(msg))

def build_error_message(msg):
    ex_type, ex, tb = sys.exc_info()
    return "\n".join([msg, str(ex)] + traceback.format_tb(tb))

def build_error(msg, view_id=None):
    ret = {'category': 'error', 'message': msg}
    if view_id is not None:
        ret['id'] = view_id
    return ret

def build_json_msg(msg):
    return (ujson.dumps(msg)+';').encode('utf-8')


if __name__ == '__main__':


    a = {'a': {'aa': 1,'ab': [2],'ac': {'aca': 3,'acb': 'd'}},
         'b': 4,
         'c': 'f'}

    b = {'a': {'ac': {'bca': 5}},
         'b': 6}

    result = dict_merge([a, b])
    print(result)

    tags = {'{{asset}}':'adcc'}

    print(template_recurse({'a':'{{asset}} Name'}, tags))
    print(template_recurse({'a':['{{asset}} Name',{'b': '{{asset}} Vol','c':4}]}, tags))

