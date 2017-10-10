import os
import pdb
import sys
import ujson
import logging
import traceback
import threading

import networkx

from views import viewtools
from views import datahandler

from views.jsonviews import HighChartsViewBuilder
from views.mplviews import MPLViewBuilder
from views.htmlviews import HTMLViewBuilder


def build_dependency_graph(views, data_provider):

    ret = networkx.DiGraph()

    for i, view in enumerate(views):

        handler_name = view.get('handler', 'raw')
        ret.add_node(i, typ='view', done=False, handler=handler_name)

        for seriesgroup in view['series']:

            tags = viewtools.dict_merge([view['tags'], seriesgroup])

            series_label = tags.pop('label')
            sg_key = viewtools.freeze_tags(tags)

            ret.add_node(sg_key, typ='seriesgroup', done=False)
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

    def get_view(self, viewtype):

        if viewtype not in self.views:
            msg = 'Unknown viewtype "{}" - valid options are: {}'
            raise RuntimeError(msg.format(viewtype, sorted(self.views.keys())))

        return self.views[viewtype]

    def build_views(self, viewlist, result_queue):
        """
        Extract all the series names so we can query them in one go.
        Data manipulators generate queries that are then passed on for execution.
        The dependency graph goes like:
        panel --> seriesgroup --> series --> query
        """
        deps = build_dependency_graph(viewlist, self.data_provider)
        nodes = deps.nodes

        series_deps = [k for k, v in nodes.items() if v['typ']=='series']
        sent_to_client = set()

        if not series_deps:
            return ujson.dumps(viewtools.build_error("No queries were generated"))

        if not networkx.is_directed_acyclic_graph(deps):
            return ujson.dumps(viewtools.build_error("Circular dependencies found"))

        def callback(sim_series, result, currentIndex, maxIndex):
            logging.debug('Callback for {}: {}/{}'.format(sim_series, currentIndex+1, maxIndex))

            try:

                nodes[sim_series]['done'] = True
                nodes[sim_series]['data'] = result

                result_queue.put({'category': 'status', 'index': currentIndex, 'maxIndex': maxIndex})

                # This iterates first through all queries, then series, seriesgroups and views
                for name in networkx.topological_sort(deps):
                    node = nodes[name]

                    if node['typ'] == 'query':
                        continue

                    # Check all dependencies are done
                    if not all(nodes[n]['done'] for n in deps.predecessors(name)):
                        continue

                    # Mark this node as done
                    node['done'] = True

                    # Propagate the data up the graph
                    if node['typ'] == 'series':
                        node['data'] = nodes[name[0]]['data']
                        continue

                    if node['typ'] == 'seriesgroup':
                        node['data'] = {n: nodes[n]['data'] for n in deps.predecessors(name)}
                        continue

                    # node type is now 'view', which has no dependents
                    view = viewlist[name]
                    view_type = view['viewtype']
                    view_generator = self.get_view(view_type)
                    view_handler = datahandler.get_handler(view.get('handler', 'raw'))

                    data_series = {}
                    for n in deps.predecessors(name):
                        data_series.update(nodes[n]['data'])

                    data_series = view_handler.process_queries(data_series)
                    view_def = view_generator.build_view(view_type, view['tags'], data_series, view['viewoptions'])

                    for series_id in data_series:
                        if series_id in sent_to_client:
                            continue
                        sent_to_client.add(series_id)
                        result_queue.put({'category': 'data', 'series': series_id, 'data': data_series[series_id]})

                    result_queue.put({'id': name, 'category': 'graph', 'result': view_def})

            except Exception:
                ex_type, ex, tb = sys.exc_info()
                logging.error('Error in callback: {}\n{}'.format(ex, "\n".join(traceback.format_tb(tb))))

        # We query for results in a different thread so we can return results in this one
        def worker():
            self.data_provider.get_view_data(series_deps, callback)
            result_queue.put(None) # Indicates the end of the data

        worker_thread = threading.Thread(target=worker)
        worker_thread.start()
        return worker_thread

    def set_data_provider(self, provider):
        self.data_provider = provider

