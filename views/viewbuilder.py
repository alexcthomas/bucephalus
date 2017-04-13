import os, pdb
import ujson

from jsonviews import HighChartsViewBuilder
from mplviews import MPLViewBuilder


class ViewBuilder(object):
    """
    class for building and providing view definitions
    can do things like auto-rebuild when files change
    """
    def __init__(self, dataprovider):
        jsonpath = os.path.realpath(os.path.join('static','views'))

        self.hcviews = HighChartsViewBuilder(jsonpath)
        self.mplviews = MPLViewBuilder()

        self.dataprovider = dataprovider

        self.check_views()

    def check_views(self):
        extra_views = set(self.hcviews.list_views()) & set(self.mplviews.list_views())
        if len(extra_views):
            msg = ','.join(extra_views)
            raise RuntimeError('Found duplicated views: {}'.format(msg))

    def build_view(self, viewname, tags, **kwargs):
        """
        uses tags to look up data
        then combines that with the view definition
        """
        if self.hcviews.has_view(viewname):
            provider = self.hcviews
        elif self.mplviews.has_view(viewname):
            provider = self.mplviews

        data = self.dataprovider.get_view_data(tags, **kwargs)

        ret = provider.build_view(viewname, tags, data, **kwargs)

        return ujson.dumps(ret)

    def set_data_provider(self, provider):
        self.dataprovider = provider

    def reload_views(self):
        self.hcviews.reload_views()