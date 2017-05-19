import numpy as np, pdb
import pandas as pd
import datetime
import PQTrading
from views.viewtools import encode_series, encode_pandas_series
from StrategyBuilder import SimLoader
from SimTools import SimulationStore
import logging


class ViewDataProvider(object):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    """
    This class maps from tags to datasets
    Could be e.g. from a database
    """
    def __init__(self, server, factory):
        logging.info("Connecting to {}".format(server))
        self._loader = SimLoader(server)
        self._factory = factory

        # Default to the latest token retrieved
        # self._token = self.get_tokens()[0]

        # Use the token with updated tags
        self._token = '[Full.Pegasus:20170516T115847.470424,1]'

    def get_tokens(self):
        tokens = self._loader.getRunTokens(datetime.datetime(1990, 1, 1), datetime.datetime.utcnow())
        return [t[0] for t in sorted(tokens, key=lambda x: x[1], reverse=True)]

    def set_token(self, token):
        logging.debug('Changing token to %s', token)
        self._token = token

    def get_view_data(self, series_list, callback):
        """
        Loads multiple data series from the database, calling callback(name, series) for each one
        :param series_list: a list of strings - the names of the series to load
        :param callback: a function that ill be called callback(name, sedries) once for each series
        :return: None
        """
        logging.debug('Calling getRunData: %s', series_list)
        self._loader.getRunData(self._token, series_list, callback)


    # Create a list of all instruments in simulations using the price data
    def get_instruments(self):
        global meta_obj
        meta_obj = self._loader.getRunMeta(self._token)
        price_obj = meta_obj.match({'category': 'asset'})
        vol_obj = meta_obj.match({'category': 'volatility'})

        price_keys = sorted(price_obj.nodes.keys())
        vol_keys = sorted(vol_obj.nodes.keys())
        # pdb.set_trace()
        return price_keys, vol_keys

    def get_trading_sys(selfs):
        trading_obj = meta_obj.match({'category':'tradingsystem'})
        return sorted(trading_obj.group('systemName').keys())