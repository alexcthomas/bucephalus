
def buildPage(title, views, tags=None, nodes=None):
    ret = {"text": title, "tags": tags, "views": views, "nodes": nodes}
    return ret


def buildViews(viewtype, tag, row):
    ret = {"viewtype": viewtype, "tags": tag, "row": row}
    return ret


def buildTags(datatype, series=None, market=None):
    ret = {"datatype": datatype, "series": series, "market": market}
    return ret