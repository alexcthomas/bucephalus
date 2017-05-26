
def buildPage(title, views=None, tags=None, nodes=None):
    ret = {"text": title, "tags": tags, "views": views, "nodes": nodes}
    return ret


def buildViews(viewtype=None, tag=None, row=None):
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


def buildTags(datatype=None, series=None, start_date=None, end_date=None, market=None, axis=""):
    ret = {"datatype": datatype, "series": series, "start_date": start_date, "end_date": end_date,
           "market": market, "axis": axis}
    return ret