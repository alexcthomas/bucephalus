import logging
import operator
import datetime

import numpy as np
import pandas as pd

from viewbuilder import SimulatorQuery, split_series

import PQTrading


class RawManipulator(object):
    PREFIX = 'raw'

    def generate_queries(self, manipulator, specifier, tags):
        start = tags['start_date']
        end = tags['end_date']
        if start is not None and end is not None:
            start = datetime.datetime.strptime(start, '%Y%m%d')
            end = datetime.datetime.strptime(end, '%Y%m%d')
            return [SimulatorQuery(specifier, start, end)], (manipulator, specifier, tags)
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
        """
        Results contains an single array of arrays, 1st column is date, 2nd column is return
        Calculate cumulative sum for returns
        """
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
        """
        Generates all the queries required to plot the graph
        """
        all_markets = [i for i in self._data_provider.get_instruments() if not i.startswith("Spread")]
        return [SimulatorQuery(name+'.prices', datetime.datetime(1978,1,1), datetime.datetime(1978, 3, 31)) for name in all_markets], None

    def process_queries(self, token, results):
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


class StratManipulator(object):
    PREFIX = 'tradingsystem'

    def __init__(self, data_provider, sys_to_subsys):
        self._data_provider = data_provider
        self._sys_to_subsys = sys_to_subsys

    def generate_queries(self, manipulator, specifier, tags):
        """
        Generates all the queries required to plot the graph
        """
        start = tags['start_date']
        end = tags['end_date']
        queries = []
        if start is not None and end is not None:
            start = datetime.datetime.strptime(start, '%Y%m%d')
            end = datetime.datetime.strptime(end, '%Y%m%d')
        instrument, sys = split_series(specifier)
        all_markets = [i for i in self._data_provider.get_instruments() if not i.startswith("Spread")]

        if 'all' == instrument and any(sys in subsys for subsys in self._sys_to_subsys.values()):
            # If specific instruments are not given, loop through all instruments given a certain sub trading system
            # Sort the instruments by sector
            instrument_list = groupBySector(all_markets)
            queries = [SimulatorQuery(i + 'Combiner.' + sys, start, end) for i in instrument_list]

        elif sys in self._sys_to_subsys.keys():
            # If given a specific instrument, but only a trading system category,
            # loop through all sub-systems within the system
            if start is None and end is None:
                queries = [SimulatorQuery(instrument + 'Combiner.' + s) for s in self._sys_to_subsys[sys]]
            else:
                queries = [SimulatorQuery(instrument + 'Combiner.' + s, start, end) for s in self._sys_to_subsys[sys]]
            instrument_list = [instrument]
        return queries, instrument_list

    def process_queries(self, token, results):
        """
        Divide data (i.e. results) into buckets, in order to be plotted as bar chart
        token: sorted list of instruments by sector
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


class SectorManipulator(object):
    PREFIX = 'sector'

    def __init__(self, data_provider):
        self._data_provider = data_provider

    def generate_queries(self, manipulator, specifier, tags):
        all_markets = [i for i in self._data_provider.get_instruments() if not i.startswith("Spread")]
        sector_to_instruments = sectorDict(all_markets)

        sector = specifier.split(".")[0]
        pnl_type = specifier.split(".")[1]

        queries = [SimulatorQuery(i + 'FinalPL.{}'.format(pnl_type)) for i in sector_to_instruments[sector]]
        return queries, (manipulator, specifier, tags)

    def process_queries(self, token, results):
        """
        :param token: not used
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


class StackManipulator(object):
    PREFIX = 'stack'

    def __init__(self, data_provider):
        self._data_provider = data_provider

    def generate_queries(self, manipulator, specifier, tags):
        sector = specifier.split(".")[0]
        pnl_type = specifier.split(".")[1]
        assert(sector == 'all')

        start = tags['start_date']
        end = tags['end_date']
        if start is not None and end is not None:
            start = datetime.datetime.strptime(start, '%Y%m%d')
            end = datetime.datetime.strptime(end, '%Y%m%d')
        all_markets = [i for i in self._data_provider.get_instruments() if not i.startswith("Spread")]

        queries = [SimulatorQuery(i + 'FinalPL.{}'.format(pnl_type), start, end) for i in all_markets]
        return queries, (manipulator, specifier, tags)

    def process_queries(self, token, results):
        '''

        :param token: (manipulator, specifier, tags), not used here
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


def sectorDict(all_markets):
    sector_to_instruments = {}
    for i in all_markets:
        sector_code = PQTrading.instrumentToSector[i[:3]]
        sector = PQTrading.sectorCodeToName[sector_code]
        sector_to_instruments[sector] = sector_to_instruments.get(sector, []) + [i]
    return sector_to_instruments


def groupBySector(all_markets):
    """
    :param all_markets: list of instrument codes (e.g. ADCC1 etc.)
    :return: a sorted list of instrument codes by their sector
    """
    sector_to_instruments = sectorDict(all_markets)
    sorted_markets = []
    for sector in sorted(sector_to_instruments.keys()):
        sorted_markets += [i for i in sector_to_instruments[sector]]
    return sorted_markets
