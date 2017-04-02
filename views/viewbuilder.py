import os
from jsonviews import JSONViewBuilder
from mplviews import MPLViewBuilder
from snsviews import SNSViewBuilder
import numpy as np
import ujson

class ViewBuilder(object):
    """
    class for building and providing JSON view definitions
    can do things like auto-rebuild when files change
    """
    def __init__(self):
        jsonpath = os.path.realpath(os.path.join('static','views'))
        self.jsonviews = JSONViewBuilder(jsonpath)
        self.mplviews = MPLViewBuilder()
        self.snsviews = SNSViewBuilder()

    def overview_bar(self, data):
        ret = self.jsonviews.get_view('overview_bar')
        ret['series'] = data
        return ujson.dumps(ret)

    def overview_distribution(self, data):
        return self.snsviews.get_view('overview_distribution', data)

    def build_view(self, viewname, tags):
        """
        uses tags to look up data
        then combines that with the view definition
        """

        if viewname == "overview_bar":
            series = [{
                        'name': 'Year 1800',
                        'data': [107, 31, 635, 203, 2]
                    }, {
                        'name': 'Year 1900',
                        'data': [133, 156, 947, 408, 6]
                    }, {
                        'name': 'Year 2012',
                        'data': [1052, 954, 4250, 740, 38]
                    }]
            return self.overview_bar(series)

        if viewname == "overview_distribution":
            series = np.random.randn(1000)
            return ujson.dumps({})
            return self.overview_distribution(series)
            return self.overview_distribution(series)
#        if viewname == "overview_bar":



#    def get_view(viewname):
#        """
#        uses
#        """
#        pass
