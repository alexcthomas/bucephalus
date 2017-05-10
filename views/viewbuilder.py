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


def get_series(graph):
    logging.debug('get_series on %s', graph)
    return [s.strip() for s in graph['tags']['series'].split(',')]


class Dependency(object):
    """
    Helper class to track dependencies.  The counter is the number of things waiting on this - when it reaches
    zero then we know that all dependencies have been met.
    """
    def __init__(self, json):
        self._json = json
        self._count = 0

    def increment(self):
        self._count += 1

    def decrement(self):
        self._count -= 1
        assert(self._count >= 0)
        return self._count == 0

    @property
    def json(self):
        return self._json


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

        self.data_provider = dataprovider

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
        series_dependency = defaultdict(list)
        all_series = []
        encountered_series = set()
        for category in jsonlist:
            for graph in category:
                # Series is either a single name or a comma-separated sequence of names
                # Ensure names are in graph order, but each only appears once
                view_type = graph['viewtype']
                dependency = Dependency(graph)
                for s in get_series(graph):
                    series_dependency[s].append(dependency)
                    dependency.increment()
                    if s in encountered_series:
                        continue
                    encountered_series.add(s)
                    all_series.append(s)

        if len(all_series) == 0:
            return ujson.dumps(build_error("No series were requested"))

        # Generate the metadata for the graphs - the layout type etc.  This runs in a callback in a different thread
        loaded_results = {}
        sent_to_client = set()

        def callback(series, data, currentIndex, maxIndex):
            logging.debug('Callback for {}: {}/{}'.format(series, currentIndex, maxIndex))
            try:
                # Adjust dependencies - when the counters reach zero we know we've everything that item needs
                requisite_data_arrived = [d for d in series_dependency[series] if d.decrement()]

                # Convert the results to a usable format
                loaded_results[series] = data
                if data is not None:
                    dates, value = zip(*data)
                    s = pd.Series(value, index=dates)
                    loaded_results[series] = encode_pandas_series(s)
                else:
                    loaded_results[series] = None

                # Determine which graphs can be built (as we've received all the necessary data).  Note
                # that viewtype below is "volatility" or "prices" - a high-level description, rather than
                # a specific renderer (i.e. not "highcharts" or similar)
                for dep in requisite_data_arrived:
                    viewtype = dep.json['viewtype']
                    tags = dep.json['tags']
                    data = {s: loaded_results[s] for s in get_series(dep.json)}
                    viewGenerator = self.views.get(viewtype)
                    if not viewGenerator:
                        raise RuntimeError('Unknown viewtype "{}" - valid options are: {}'.format(viewtype,
                            ", ".join(self.views.keys())))
                    result, data_series = viewGenerator.build_view(viewtype, tags, data)

                    # Send any NEW names back to the client - note that this means that if you MAKE UP any new
                    # data, you've got to give it a NEW name.  Also - no mutating data sets!
                    if data_series is not None:
                        for series_name, data in data_series.items():
                            if series_name in sent_to_client:
                                continue
                            sent_to_client.add(series_name)
                            result_queue.put({'category': 'data', 'series': series_name, 'data': data})

                    result_queue.put({'category': 'graph', 'result': result})
            except Exception:
                ex_type, ex, tb = sys.exc_info()
                logging.error('Error in callback: {}\n{}'.format(ex, "\n".join(traceback.format_tb(tb))))

        # We query for results in a different thread so we can return results in this one
        def worker():
            self.data_provider.get_view_data(all_series, callback)
            result_queue.put(None)      # Used to mark the end of the data
        worker_thread = threading.Thread(target=worker)
        worker_thread.start()
        return worker_thread

    def set_data_provider(self, provider):
        self.data_provider = provider

    def reload_views(self):
        self.hcviews.reload_views()