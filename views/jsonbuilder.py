
def buildPage(title, views, tags=None, nodes=None):
    ret = {"text": title, "tags": tags, "views": views, "nodes": nodes}
    return ret


def buildViews(viewtype, tag, row):
    """
    Creates a view of the specified type.  Note that you specify a view like "volatility" or
    "overview_distribution", which in the case of Highcharts graphs, refers to a JSON File, 
    and in the case of Matplotlib graphs refers to an entry at the top of the MplViewBuilder class.
    
    :param viewtype: the name of the view type - this is a high-level type like "volatility"
    :param tag: the tags to attach (arbitrary)
    :param row: the index of the row, starting at 1.
    :return: an object ready for conversion into JSON for the client
    """
    ret = {"viewtype": viewtype, "tags": tag, "row": row}
    return ret


def buildTags(datatype, series=None, market=None, axis=""):
    ret = {"datatype": datatype, "series": series, "market": market, "axis": axis}
    return ret