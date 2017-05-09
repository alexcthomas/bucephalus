import os, sys, pdb
import traceback
import ujson

from views.viewtools import build_error

from views.jsonviews import HighChartsViewBuilder
from views.mplviews import MPLViewBuilder
from views.htmlviews import HTMLViewBuilder


class ViewBuilder(object):
    """
    class for building and providing view definitions
    can do things like auto-rebuild when files change
    """
    def __init__(self, dataprovider):
        jsonpath = os.path.realpath(os.path.join('static','views'))

        self.viewproviders = [HighChartsViewBuilder(jsonpath),
                                MPLViewBuilder(),
                                HTMLViewBuilder()]

        self.dataprovider = dataprovider

        self.check_views()
        self.prepare_views()

    def check_views(self):
        viewsets = [set(vp.list_views()) for vp in self.viewproviders]
        extra_views = set.intersection(*viewsets)
        if len(extra_views):
            msg = ','.join(extra_views)
            raise RuntimeError('Found duplicated views: {}'.format(msg))

    def prepare_views(self):
        self.views = {}
        for vp in self.viewproviders:
            for v in vp.list_views():
                self.views[v] = vp

    def build_view(self, viewname, tags, **kwargs):
        """
        uses tags to look up data
        then combines that with the view definition
        """

        if viewname not in self.views:
            msg = 'View {} not found'.format(viewname)
            return ujson.dumps(build_error(msg))

        try:

            data = self.dataprovider.get_view_data(tags, **kwargs)
            ret = self.views[viewname].build_view(viewname, tags, data, **kwargs)
        except Exception:
            ex_type, ex, tb = sys.exc_info()
            msg = 'Error: {}\n'.format(ex)
            msg += "\n".join(traceback.format_tb(tb))
            ret = build_error(msg)

        return ujson.dumps(ret)

    def build_views(self, jsonlist):
        all_series = []
        for category in jsonlist:
            for graph in category:
                all_series.append(graph['tags']['series'])

        if len(all_series) == 0:
            return ujson.dumps(build_error("Empty data"))

        new_tag = {'datatype': 'series', 'series': all_series}
        ret = []
        try:
            dataForGraphs = self.dataprovider.get_view_data(new_tag)
            for data in dataForGraphs:
                market = data['name'].split('.')[0]
                market = market.split('Position')[0]
                viewname = data['name'].split('.')[1]
                viewname = 'price' if viewname == 'prices' else viewname
                tags = {'datatype': viewname, 'series': data['name'], 'market': market}
                ret.append({data['name']: self.views[viewname].build_view(viewname, tags, [data])})
        except Exception:
            ex_type, ex, tb = sys.exc_info()
            msg = 'Error: {}\n'.format(ex)
            msg += "\n".join(traceback.format_tb(tb))
            ret = build_error(msg)

        return ujson.dumps(ret)

        # Extract all the series names from the JSON, building an array suitable for sending
        # to the SimLoader.

        # Return a dictionary with each location:
        # { 0: ..., 1: ...} - this can then be unpacked on the client side

    def set_data_provider(self, provider):
        self.dataprovider = provider

    def reload_views(self):
        self.hcviews.reload_views()