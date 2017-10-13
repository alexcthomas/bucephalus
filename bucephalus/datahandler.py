import logging, pdb

import numpy as np

handlers = {}


def register(cls):
    handlers[cls.name] = cls
    return cls


def get_handler(hdlr):
    return handlers[hdlr]


class BaseHandler(object):
    pass


@register
class RawHandler(BaseHandler):
    name = 'raw'

    @classmethod
    def process_queries(cls, results):
        """
        We are passed a map from query -> data.  We "process" this by simply returning the data.
        """
        return results


@register
class AccumulateHandler(RawHandler):
    name = 'accumulate'

    @classmethod
    def process_queries(cls, results):
        """
        Results contains an single array of arrays, 1st column is date, 2nd column is return
        Calculate cumulative sum for returns
        """
        ret = []
        for k, v in results:
            values = v.copy() # don't modify the original data
            values.values[:, 1] = values.values[:, 1].cumsum(axis=0)
            ret.append((k+(cls.name,), values))

        return ret


@register
class CorrelationHandler(BaseHandler):
    name = 'correlation'

    @classmethod
    def process_queries(cls, results):
        """
        Loop through results to calculate the correlation between any two assets
        """
        keys = sorted(list(results.keys()), key=lambda q: q.name)
        correl = []
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


