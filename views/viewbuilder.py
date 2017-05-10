import os
import sys
import traceback
import threading
import pandas as pd
import logging
import ujson

from collections import defaultdict
from views.viewtools import build_error
from views.viewtools import encode_pandas_series
from views.jsonviews import HighChartsViewBuilder
from views.mplviews import MPLViewBuilder
from views.htmlviews import HTMLViewBuilder
import PQTrading


def get_series(graph):
    logging.debug('get_series on %s', graph)
    return [s.strip() for s in graph['tags']['series'].split(',')]

class ViewBuilder(object):
    """
    class for building and providing view definitions
    can do things like auto-rebuild when files change
    """
    def __init__(self, dataprovider):
        jsonpath = os.path.realpath(os.path.join('static', 'views'))

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
                logging.debug('View provider [%s] -> %s', v, vp)
                self.views[v] = vp

    def build_views(self, jsonlist, result_queue):
        # Extract all the series names so we can query them in one go.  Build a map so we can
        # jump between a series name and the definitions that it enables.
        last_series_for_graph = defaultdict(list)
        all_series = []
        encountered_series = set()
        send_to_client = set()
        for category in jsonlist:
            for graph in category:
                # Series is either a single name or a comma-separated sequence of names
                # Ensure names are in graph order, but each only appears once
                viewtype = graph['viewtype']
                for s in get_series(graph):
                    if self.views[viewtype].requires_client_data():
                        send_to_client.add(s)
                    if s in encountered_series:
                        continue
                    encountered_series.add(s)
                    all_series.append(s)

                # At the point we receive the last item added we know we have all the data we require
                last_series_for_graph[all_series[-1]].append(graph)

        if len(all_series) == 0:
            return ujson.dumps(build_error("No series were requested"))

        # Generate the metadata for the graphs - the layout type etc.  This runs in a callback in a different thread
        loaded_results = {}

        def callback(series, data, currentIndex, maxIndex):
            logging.debug('Callback for {}: {}/{}'.format(series, currentIndex, maxIndex))
            try:
                # Send the result block if anyone needs it
                if series in send_to_client:
                    result_queue.put({'category': 'data', 'series': series, 'data': data})
                loaded_results[series] = data

                dates, value = zip(*data)
                s = pd.Series(value, index=dates)
                loaded_results[series] = encode_pandas_series(s)

                # Determine which graphs can be built (as we've received all the necessary data).  Note
                # that viewtype below is "volatility" or "prices" - a high-level description, rather than
                # a specific renderer (i.e. not "highcharts" or similar)
                for graph in last_series_for_graph[series]:
                    logging.debug('Graph definition: %s', graph)
                    viewtype = graph['viewtype']
                    tags = graph['tags']
                    data = {s: loaded_results[s] for s in get_series(graph)}
                    viewGenerator = self.views.get(viewtype)
                    if not viewGenerator:
                        raise RuntimeError('Unknown viewtype "{}" - valid options are: {}'.format(viewtype,
                            ", ".join(self.views.keys())))
                    result_queue.put({'category': 'graph', 'result': viewGenerator.build_view(viewtype, tags, data)})
            except Exception:
                ex_type, ex, tb = sys.exc_info()
                logging.error('Error in callback: {}\n{}'.format(ex, "\n".join(traceback.format_tb(tb))))

        # We query for results in a different thread so we can return results in this one
        def worker():
            self.dataprovider.get_view_data(all_series, callback)
            result_queue.put(None)      # Used to mark the end of the data
        worker_thread = threading.Thread(target=worker)
        worker_thread.start()
        return worker_thread

    def set_data_provider(self, provider):
        self.dataprovider = provider

    def reload_views(self):
        self.hcviews.reload_views()