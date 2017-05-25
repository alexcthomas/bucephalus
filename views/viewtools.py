import copy, pdb
import pandas as pd
import logging

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
    return list(zip(dates.astype(int)/1000000, data))

def encode_pandas_series(series):
    try:
        ret = pd.Series(series.values, series.index.astype(int)/1000000)
        return ret.reset_index().values
    except:
        return series.values

def build_error(msg):
    return {'error': msg.replace('\n','<br/>')}

