import os
import pdb
import sys
import traceback
import threading
import pandas as pd
import logging
import ujson
import collections
from datamanipulator import *
import numpy as np

from collections import defaultdict
from views.viewtools import build_error
from views.viewtools import encode_pandas_series
from views.jsonviews import HighChartsViewBuilder
from views.mplviews import MPLViewBuilder
from views.htmlviews import HTMLViewBuilder


def get_series(graph):
    logging.debug('get_series on %s', graph['tags']['series'])
    return [s.strip() for s in graph['tags']['series'].split(',')]


class Dependency(object):
    """
    Helper class to track dependencies.  The counter is the number of things waiting on this - when it reaches
    zero then we know that all dependencies have been met.
    """
    def __init__(self, token):
        self._token = token
        self._count = 0

    def increment(self):
        self._count += 1

    def decrement(self):
        self._count -= 1
        assert(self._count >= 0)
        return self._count == 0

    @property
    def token(self):
        return self._token


def split_series(series):
    """
    Split series into two parts: manipulator (usually prefix) and specifier (usually suffix)
    """
    index = series.find(":")
    if -1 == index:
        raise Exception("Colon not found in series '{}'.".format(series))
    manipulator = series[:index]
    specifier = series[index+1:]
    return manipulator, specifier


class SimulatorQuery(object):
    def __init__(self, name, start=None, finish=None):
        self._name = name
        self._start = start
        self._finish = finish

    @property
    def name(self):
        return  self._name

    @property
    def start(self):
        return self._start

    @property
    def finish(self):
        return self._finish

    def __hash__(self):
        return hash((self._name, self._start, self._finish))

    def __eq__(self, other):
        return self._name, self._start, self._finish == other._name, other._start, other._finish


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
        """
        Extract all the series names so we can query them in one go.
        Data manipulators generate queries that are then passed on for execution.
        General design of the function:
            {queries} --(depends)--> manipulator --(generates)--> manipulated data
            {manipulated data} --(depends)--> graph
        """
        query_dependency = defaultdict(list)
        series_dependency = defaultdict(list)
        counter = 0
        sys_to_subsys = self.data_provider.get_trading_sys()
        manipulators = {
            RawManipulator.PREFIX: RawManipulator(),
            AccumManipulator.PREFIX: AccumManipulator(),
            CorrelManipulator.PREFIX: CorrelManipulator(self.data_provider),
            StratManipulator.PREFIX: StratManipulator(self.data_provider, sys_to_subsys),
            SectorManipulator.PREFIX: SectorManipulator(self.data_provider),
            StackManipulator.PREFIX: StackManipulator(self.data_provider)
        }

        for row in jsonlist:
            for graph in row:
                # Track dependencies between data series and graphs.
                # As one graph might depend on several data series (tracked by counter).
                series_dep = Dependency((graph, counter))
                counter += 1
                for s in get_series(graph):
                    # For each graph to be plotted, generate a list queries required for retrieving data from
                    # simulation, manipulate the data if required
                    manipulator_name, specifier = split_series(s)
                    manipulator = manipulators.get(manipulator_name)
                    if manipulator is None:
                        raise RuntimeError("Manipulator '{}' doesn't exist.".format(manipulator_name))

                    queries, token = manipulator.generate_queries(manipulator_name, specifier, graph['tags'])
                    # Track dependencies between manipulators and queries,
                    # as data from one data manipulation might depend on data from several queries
                    manipulator_dep = Dependency((manipulator, token, s, queries))

                    # For both queries and data series, record their dependency object (graphs or manipulation)
                    # in the dictionary, increase the count of their dependency
                    series_dependency[s].append(series_dep)
                    series_dep.increment()
                    for q in queries:
                        query_dependency[q].append(manipulator_dep)
                        manipulator_dep.increment()

        if len(query_dependency) == 0:
            return ujson.dumps(build_error("No queries were generated"))

        # Generate the metadata for the graphs - the layout type etc.  This runs in a callback in a different thread
        loaded_results = {}
        sent_to_client = set()
        manipulator_output = {}

        # Map the simulation query name (e.g. 'ADCC1') to its query (e.g. ('ADCC1', startdate, enddate))
        queryNameToQuery = {q.name: q for q in query_dependency.keys()}

        def callback(sim_series, data, currentIndex, maxIndex):
            logging.debug('Callback for {}: {}/{}'.format(sim_series, currentIndex, maxIndex))
            query = queryNameToQuery[sim_series]
            try:
                # Convert the results to a usable format
                if data is not None and 0 != len(data):
                    dates, value = zip(*data)
                    s = pd.Series(value, index=dates)
                    loaded_results[query] = encode_pandas_series(s)
                else:
                    loaded_results[query] = None

                result_queue.put({'category': 'status', 'index': currentIndex, 'maxIndex': maxIndex})

                # Adjust dependencies - when the counters reach zero we know we've all queries that manipulator needs
                manipulator_deps = [d for d in query_dependency[query] if d.decrement()]

                for manipulator_dep in manipulator_deps:
                    # Map each query in the manipulator to its corresponding data,
                    # pass the data from all queries into data manipulator for further process
                    manipulator, token, s, queries = manipulator_dep.token
                    inputs = {q: loaded_results[q] for q in queries}
                    manipulator_output[s] = manipulator.process_queries(token, inputs)

                    # Adjust dependencies - when the counters reach zero we know we've data series a graph needs
                    series_deps = [d for d in series_dependency[s] if d.decrement()]
                    results = collections.OrderedDict()
                    for dep in series_deps:
                        # Find a graph that's ready to be plotted, find the series, then use the results received from
                        # the last for loop to retrieve manipulated data for each series
                        graph, counter = dep.token
                        for s in get_series(graph):
                            _, specifier = split_series(s)
                            results[specifier] = manipulator_output[s]

                        # Use the manipulated data to build view for the graph
                        viewtype = graph['viewtype']
                        viewGenerator = self.views.get(viewtype)
                        if not viewGenerator:
                            raise RuntimeError('Unknown viewtype "{}" - valid options are: {}'.format(
                                viewtype, ", ".join(self.views.keys())))
                        result, data_series = viewGenerator.build_view(viewtype, graph['tags'], results)

                        # Send any NEW names back to the client - note that this means that if you MAKE UP any new
                        # data, you've got to give it a NEW name.  Also - no mutating data sets!
                        if data_series is not None:
                            for series_name in data_series:
                                if series_name in sent_to_client:
                                    continue
                                sent_to_client.add(series_name)
                                data = data_series[series_name]
                                result_queue.put({'category': 'data', 'series': series_name, 'data': data})
                        result_queue.put({'id': counter, 'category': 'graph', 'result': result})

            except Exception:
                ex_type, ex, tb = sys.exc_info()
                logging.error('Error in callback: {}\n{}'.format(ex, "\n".join(traceback.format_tb(tb))))

        # We query for results in a different thread so we can return results in this one
        def worker():
            self.data_provider.get_view_data(query_dependency.keys(), callback)
            result_queue.put(None)      # Used to mark the end of the data
        worker_thread = threading.Thread(target=worker)
        worker_thread.start()
        return worker_thread

    def set_data_provider(self, provider):
        self.data_provider = provider

    def reload_views(self):
        self.hcviews.reload_views()