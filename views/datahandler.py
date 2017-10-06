import logging
import operator

import numpy as np
import pandas as pd

import PQTrading


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

    def process_queries(self, results):
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

        ret = {}
        for k, v in results.items():
            values = v.copy() # don't modify the original data
            values[:, 1] = values[:, 1].cumsum(axis=0)
            ret[k+(cls.name,)] = values

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


@register
class StrategyHandler(BaseHandler):
    name = 'tradingsystem'

    @classmethod
    def process_queries(cls, results):
        """
        Divide data (i.e. results) into buckets, in order to be plotted as bar chart
        """
        buckets = []
        queries = {}
        if 1 == len(token):
            # This is strategy page under each instrument. Use strategy as keys to retrieve results.
            for keys in list(results.keys()):
                strat = keys.name.split('.')[1]
                logging.debug('Strategy: %s', strat)
                queries[strat] = keys
            items = sorted(queries.keys())

            for item in items:
                # Loop through strategies / ordered instruments to retrieve data.
                # Note results[key] is an array of one array, we only extract the 2nd data and ignore the first (date)
                key = queries[item]
                buckets.append([item, results[key] if results[key] is not None else 0])
            return buckets

        else:
            # This is the strategy page for all instruments. Use sorted instruments as keys to retrieve results.
            for key in list(results.keys()):
                instrument = key.name.split('Combiner')[0]
                queries[instrument] = key
            items = token

            for item in items:
                # Loop through strategies / ordered instruments to retrieve data.
                # Note results[key] is an array of one array, we only extract the 2nd data and ignore the first (date)
                key = queries[item]
                buckets.append([item, results[key][0][1] if results[key] is not None else 0])
            return buckets


@register
class SectorHandler(BaseHandler):
    name = 'sector'

    @classmethod
    def process_queries(cls, results):
        """
        :param results: daily returns for each of the instruments under a certain sector
        :return: combined cumulative returns of all instruments
        """

        first = True
        # Summing up all the data together
        for instrumentPnL in results.values():
            df = pd.Series(index=[dailyPnL[0] for dailyPnL in instrumentPnL],
                           data=[dailyPnL[1] for dailyPnL in instrumentPnL])
            if first:
                # Use the first data block as the starting point as total
                total = df
                first = False
            else:
                total = total.add(df, fill_value=0)

        # Converting pandas series into numpy array and calculate the cumulative sum
        data = total.as_matrix().cumsum(axis=0)
        dates = total.index.values
        return np.column_stack((dates, data))


@register
class StackHandler(BaseHandler):
    name = 'stack'

    @classmethod
    def process_queries(cls, results):
        '''
        :param results: Daily PnL of instruments under a certain sector across a chosen date range
        :return: a dataset that maps sector to combined PnL of all instruments within the sector
        '''
        sector_pnl = {} # Unsorted map from sector code to combined PnL of its instruments

        for key in list(results.keys()):
            cum_pnl = 0  # Cumulative PnL of instrument over the chosen period of time
            instrument = key.name.split('FinalPL')[0]
            sector_code = PQTrading.instrumentToSector[instrument[:3]]

            if results[key] is not None:
                for li in results[key]:
                    cum_pnl += li[1] if li is not None else 0
            sector_pnl[sector_code] = sector_pnl.get(sector_code, 0) + cum_pnl

        dataset = []
        sorted_pnl = sorted(sector_pnl.items(), key=operator.itemgetter(1)) # Sort sector_pnl by values (i.e. PnL)
        for item in sorted_pnl:
            sector_code, pnl = item[0], item[1]
            data = {"name": PQTrading.sectorCodeToName[sector_code], "y": pnl}
            dataset.append(data)
        return dataset

