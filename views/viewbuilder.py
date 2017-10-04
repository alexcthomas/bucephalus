import os
import pdb
import sys
import ujson
import logging
import traceback
import threading
import collections

import networkx
import pandas as pd

from views import viewtools

from views.jsonviews import HighChartsViewBuilder
from views.mplviews import MPLViewBuilder
from views.htmlviews import HTMLViewBuilder

import views.datamanipulator as dm


def build_dependency_graph(views, data_provider):

    ret = networkx.DiGraph()

    for i, view in enumerate(views):

        ret.add_node(i, typ='view', done=False)

        handler_name = view['handler']
        dm.check_handler(handler_name)

        for seriesgroup in view['series']:

            tags = viewtools.dict_merge([view['tags'], seriesgroup])

            series_label = tags.pop('label')
            sg_key = viewtools.freeze_tags(tags)

            ret.add_node(sg_key, typ='seriesgroup', handler=handler_name, done=False)
            ret.add_edge(sg_key, i)

            # Get the simulation queries required, may be more than one
            series_queries = data_provider.get_series_names_from_tags(tags.copy(), series_label)

            for series in series_queries:
                ret.add_node(series, typ='series', done=False)
                ret.add_edge(series, sg_key)

                query, object_name, label = series

                # networkx ignores adding the same node twice
                # so we don't need to check if this query is already there
                ret.add_node(query, typ='query', done=False)
                ret.add_edge(query, series)

        return ret


class ViewBuilder(object):
    """
    class for building and providing view definitions
    can do things like auto-rebuild when files change
    """
    def __init__(self, data_provider):
        jsonpath = os.path.realpath(os.path.join('static', 'views'))

        self.view_providers = [HighChartsViewBuilder(jsonpath),
                               MPLViewBuilder(),
                               HTMLViewBuilder()]

        self.data_provider = data_provider

        self.check_views()
        self.prepare_views()

    def check_views(self):
        viewsets = [set(vp.list_views()) for vp in self.view_providers]
        extra_views = set.intersection(*viewsets)
        if len(extra_views):
            msg = ','.join(extra_views)
            raise RuntimeError('Found duplicated views: {}'.format(msg))

    def prepare_views(self):
        self.views = {}
        for vp in self.view_providers:
            for v in vp.list_views():
                logging.debug('View provider [%s] -> %s', v, vp)
                self.views[v] = vp

    def build_views(self, viewlist, result_queue):
        """
        Extract all the series names so we can query them in one go.
        Data manipulators generate queries that are then passed on for execution.
        The dependency graph goes like:
        panel --> seriesgroup --> series --> query
        """
        deps = build_dependency_graph(viewlist, self.data_provider)
        series_deps = [k for k, v in deps.nodes.items() if v['typ']=='series']
        sent_to_client = set()

        if not series_deps:
            return ujson.dumps(viewtools.build_error("No queries were generated"))

        if not networkx.is_directed_acyclic_graph(deps):
            return ujson.dumps(viewtools.build_error("Circular dependencies found"))

        def callback(sim_series, data, currentIndex, maxIndex):
            logging.debug('Callback for {}: {}/{}'.format(sim_series, currentIndex, maxIndex))

            result = viewtools.parse_result_series(data)

            deps.nodes[sim_series]['done'] = True
            deps.nodes[sim_series]['data'] = result

            result_queue.put({'category': 'status', 'index': currentIndex, 'maxIndex': maxIndex})

            for name in networkx.topological_sort(deps):
                node = deps.nodes[name]

                if node['typ'] == 'query':
                    continue

                if not all(deps.nodes[n]['done'] for n in deps.predecessors(name)):
                    continue

                node['done'] = True

                if node['typ'] != 'view':
                    continue

                pdb.set_trace()
                view = viewlist[name]

                # Find a graph that's ready to be plotted, find the series,
                # then use the results received from
                # the last for loop to retrieve manipulated data for each series
                for s in get_series(graph):
                    _, specifier = dm.split_series(s)
                    results[specifier] = manipulator_output[s]

                # Use the manipulated data to build view for the graph
                viewtype = view['viewtype']
                view_generator = self.views.get(viewtype)

                if not view_generator:
                    msg = 'Unknown viewtype "{}" - valid options are: {}'
                    raise RuntimeError(msg.format(viewtype, self.views.keys()))

                result, data_series = view_generator.build_view(viewtype, view['tags'], results)

                # Send any new series back to the client
                if data_series is not None:
                    for series_name in data_series:
                        if series_name in sent_to_client:
                            continue
                        sent_to_client.add(series_name)
                        data = data_series[series_name]
                        result_queue.put({'category': 'data', 'series': series_name, 'data': data})

                result_queue.put({'id': name, 'category': 'graph', 'result': result})

        # We query for results in a different thread so we can return results in this one
        def worker():
            self.data_provider.get_view_data(series_deps, callback)
            result_queue.put(None)      # Indicates the end of the data

        worker_thread = threading.Thread(target=worker)
        worker_thread.start()
        return worker_thread

    def set_data_provider(self, provider):
        self.data_provider = provider

    def reload_views(self):
        self.view_providers[0].reload_views()

