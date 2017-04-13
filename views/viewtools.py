import copy, pdb

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
    for k, v in merge_dct.iteritems():
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
    "Recursively applies string templating to a dict or list"
    if isinstance(tmpl, basestring):
        ret = tmpl
        for k,v in tags.iteritems():
            ret = ret.replace(k, v)
        return ret

    if isinstance(tmpl, list):
        return [template_recurse(v, tags) for v in tmpl]

    if isinstance(tmpl, dict):
        return {k:template_recurse(v, tags) for k, v in tmpl.iteritems()}

    return tmpl

def encode_series(dates, data):
    return list(zip(dates.astype(int)/1000000, data))


if __name__ == '__main__':


    a = {'a': {'aa': 1,'ab': [2],'ac': {'aca': 3,'acb': 'd'}},
         'b': 4,
         'c': 'f'}

    b = {'a': {'ac': {'bca': 5}},
         'b': 6}

    result = dict_merge([a, b])
    print result
#    pdb.set_trace()

    tags = {'{{asset}}':'adcc'}

    print template_recurse({'a':'{{asset}} Name'}, tags)
    print template_recurse({'a':['{{asset}} Name',{'b': '{{asset}} Vol','c':4}]}, tags)
