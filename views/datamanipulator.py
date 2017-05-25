import datetime
import numpy as np
import logging
import pdb
from viewbuilder import SimulatorQuery


class RawManipulator(object):
    PREFIX = 'raw'

    def generate_queries(self, manipulator, specifier, tags):

        start = tags['start_date']
        end = tags['end_date']
        if start is not None and end is not None:
            start = datetime.datetime.strptime('%Y%m%d', start)
            end = datetime.datetime.strptime('%Y%m%d', end)
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
