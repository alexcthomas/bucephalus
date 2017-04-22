import os, sys, pdb
import traceback
import ujson

from viewtools import build_error

from jsonviews import HighChartsViewBuilder
from mplviews import MPLViewBuilder
from htmlviews import HTMLViewBuilder


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
            msg += traceback.format_exc(tb)
            ret = build_error(msg)

        return ujson.dumps(ret)

    def set_data_provider(self, provider):
        self.dataprovider = provider

    def reload_views(self):
        self.hcviews.reload_views()