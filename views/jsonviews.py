import os, copy, pdb
import ujson, yaml
import logging
import pandas as pd
import datetime as dt
import numpy as np
from views.baseviews import BaseViewBuilder
from views.viewtools import dict_merge, template_recurse
import collections


class JSONView(object):
    """
    Class representing an individual json view
    provides functionality for recursively building from prototypes
    and applying tags as template arguments
    """
    def __init__(self, name, mtime, path, typ, builder):
        self.name = name
        self.mtime = mtime
        self.path = path
        self.typ = typ
        self.builder = builder
        self.compiled = False
        self.prototypes = []
        self.read_view()

    def read_view(self):
        """
        Reads the view from a file
        Two formats are supported:
            Raw, where the name is given by the file name and there are no prototypes
            Enclosed, where prototypes can be provided
        """
        with open(self.path, 'r') as fh:
            if self.typ == 'json':
                result = ujson.load(fh)
            if self.typ == 'yaml':
                result = yaml.load(fh)

        # raw
        if 'viewDefinition' not in result:
            self.view_def = result
            self.compiled = True
            return

        # enclosed
        self.view_def = result['viewDefinition']
        if 'prototypes' in result and result['prototypes']:
            self.prototypes = result['prototypes'].split(',')
        else:
            self.compiled = True

    def build(self, force=False):
        """
        Makes sure all prototypes have been built then derives from them
        """
        if self.compiled and not force:
            return

        for p in self.prototypes:
            self.builder.views_cache[p].build(force)

        to_merge = [self.builder.get_view(n).view_def for n in self.prototypes]
        self.view_def = dict_merge(to_merge+[self.view_def])
        self.compiled = True

    def render_tags(self, tags):
        """
        Recursively apply given tags as template arguments
        """
        tmpl_tags = {'{{'+k+'}}':v for k,v in tags.items()}
        tmpl = copy.deepcopy(self.view_def)
        return template_recurse(tmpl, tmpl_tags)


class JSONViewBuilder(BaseViewBuilder):
    """
    class for building and providing view definitions
    can do things like auto-rebuild when files change
    """

    def __init__(self, loc):
        self.location = loc
        self.views_cache = {}
        self.allowed_types = ['json', 'yaml']

        self.read_views()
        self.build_views()

    def read_views(self):
        """
        Reads views from file.
        Keeps track of modification time so we can reload
        only those that have changed.
        """
        logging.debug('Loading views from %s', os.path.abspath(self.location))
        for r, dirs, files in os.walk(self.location):
            for file_name in files:

                view_name, _, typ = file_name.rpartition('.')
                file_path = os.path.join(r, file_name)

                # check we accept views in that language
                if typ not in self.allowed_types:
                    continue

                mtime = os.stat(file_path).st_mtime

                # check if we have a cached version
                if view_name in self.views_cache:
                    cached = self.views_cache[view_name]

                    # check this isn't a duplicate
                    if r != cached['path']:
                        msg = 'View {}, in {} is duplicated in {}'
                        raise RuntimeError(msg.format(view_name, cached['path'], r))

                    # check this is newer than the cached copy
                    if mtime <= cached.mtime:
                        continue

                # read the view
                v = JSONView(view_name,  mtime, file_path, typ, self)
                logging.debug('Loaded view %s', view_name)
                self.views_cache[view_name] = v

    def get_view(self, name):
        if name not in self.views_cache:
            raise KeyError('View {} not found'.format(name))
        return self.views_cache[name]

    def build_views(self):
        for v in self.views_cache.values():
            v.build()

    def reload_views(self):
        self.read_views()
        self.build_views(force=True)


class HighChartsViewBuilder(JSONViewBuilder):
    """
    Contains logic for combining config details from the JSONViewBuilder
    with data from the dataprovider
    Different highcharts chart types can need the data labelled in different ways
    """

    def build_view(self, view_name, tags, data):
        view = self.views_cache[view_name]
        ret = view.render_tags(tags)
        ret['renderer'] = 'highcharts'
        logging.debug('build_view(%s, %s)', view_name, tags)

        if view_name == 'histogram':
            modified, buckets = {}, []
            # pdb.set_trace()
            keys = sorted(data.keys())
            for item in keys:
                all_prices = data[item]
                time_stamp = all_prices[0][0]
                year_start = dt.date.fromtimestamp(time_stamp/1e3)
                yearly_prices = []
                for daily_price in all_prices:
                    if dt.date.fromtimestamp(daily_price[0]/1e3) - year_start > dt.timedelta(364):
                        buckets.append([time_stamp, np.average(yearly_prices)])
                        time_stamp = daily_price[0]
                        year_start = dt.date.fromtimestamp(time_stamp/1e3)
                        yearly_prices = []
                    yearly_prices.append(daily_price[1])

            modified['annual return'] = buckets
            ret['series'] = ['annual return']

        else:
            modified = data
            ret['series'] = list(data.keys())

        return ret, modified

