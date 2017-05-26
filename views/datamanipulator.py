import datetime
import numpy as np
import logging
import pdb
from viewbuilder import SimulatorQuery, split_series


class RawManipulator(object):
    PREFIX = 'raw'

    def generate_queries(self, manipulator, specifier, tags):

        start = tags['start_date']
        end = tags['end_date']
        if start is not None and end is not None:
            start = datetime.datetime.strptime(start, '%Y%m%d')
            end = datetime.datetime.strptime(end, '%Y%m%d')
            return [SimulatorQuery(specifier, start, end)],(manipulator, specifier, tags)

        sim_query = SimulatorQuery(specifier)
        return [sim_query], (manipulator, specifier, tags)

    def process_queries(self, token, results):
        """
        We are passed a map from query -> data.  We "process" this by simply returning the data. 
        """
        assert(len(results) == 1)
        return results[list(results.keys())[0]]


class AccumManipulator(RawManipulator):
    PREFIX = 'accum'

    def process_queries(self, token, results):
        assert(len(results) == 1)
        seriesOrNone = results[list(results.keys())[0]]
        if seriesOrNone is not None:
            dates = seriesOrNone[:, 0]
            accum_ret = seriesOrNone[:, 1].cumsum(axis=0)
            return np.column_stack((dates, accum_ret))


class CorrelManipulator(object):
    PREFIX = 'correl'

    def __init__(self, data_provider):
        self._data_provider = data_provider

    def generate_queries(self, manipulator, specifier, tags):
        all_markets = [i for i in self._data_provider.get_instruments() if not i.startswith("Spread")]
        return [SimulatorQuery(name+'.prices', datetime.datetime(1978,1,1), datetime.datetime(1978, 3, 31)) for name in all_markets], None

    def process_queries(self, token, results):
        keys = sorted(list(results.keys()), key=lambda q: q.name)
        modified, correl = {}, []
        # pdb.set_trace()
        for i1, first in enumerate(keys):
            for i2, second in enumerate(keys):
                if results[first] is not None and results[second] is not None:
                    logging.debug('Processing correlation between %s and %s', first, second)
                    min_length = min(len(results[first]), len(results[second]))
                    firstData = list(list(zip(*results[first][-min_length:]))[1])
                    secondData = list(list(zip(*results[second][-min_length:]))[1])
                    correl.append([i1, i2, np.corrcoef(firstData, secondData)[0, 1]])
                else:
                    # If no data for either instrument, return correlation of 0
                    correl.append([i1, i2, 0])

        return correl


class StratManipulator(object):
    PREFIX = 'tradingsystem'

    def __init__(self, data_provider, sys_to_subsys):
        self._data_provider = data_provider
        self._sys_to_subsys = sys_to_subsys

    def generate_queries(self, manipulator, specifier, tags):
        start = tags['start_date']
        end = tags['end_date']
        queries = []
        if start is not None and end is not None:
            start = datetime.datetime.strptime(start, '%Y%m%d')
            end = datetime.datetime.strptime(end, '%Y%m%d')
        # pdb.set_trace()
        instrument, sys = split_series(specifier)
        # pdb.set_trace()
        if 'all' == instrument and any(sys in subsys for subsys in self._sys_to_subsys.values()):
            # If specific instruments are not given, loop through all instruments given a certain sub trading system
            all_markets = [i for i in self._data_provider.get_instruments() if not i.startswith("Spread")]
            queries = [SimulatorQuery(i + 'Combiner.' + sys, start, end) for i in all_markets]
        elif sys in self._sys_to_subsys.keys():
            # If given a specific instrument, but only a trading system category,
            # loop through all sub-systems within the system
            queries = [SimulatorQuery(instrument + 'Combiner.' + s, start, end) for s in self._sys_to_subsys[sys]]
        return queries, None

    def process_queries(self, token, results):
        # pdb.set_trace()
        buckets = []
        keys = sorted(list(results.keys()), key=lambda q: q.name)
        for item in keys:
            # results[item] returns an array of a single array, consisting of date and data.
            # Here we only extract the data to be appended in the buckets
            buckets.append([item.name, results[item][0][1]if results[item] is not None else 0])
        return buckets

