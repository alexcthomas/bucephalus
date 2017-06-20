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
        self._token = '[Pegasus-new:20170613T090230.296785,121]'
        # self._token = '[ibuchanan:20170523T161710.490641,1]'
        # self._token = '[Full.Pegasus:20170516T115847.470424,1]'

        self._meta_obj = self._loader.getRunMeta(self._token)

    def get_tokens(self):
        tokens = self._loader.getRunTokens(datetime.datetime(1990, 1, 1), datetime.datetime.utcnow())
        return [t[0] for t in sorted(tokens, key=lambda x: x[1], reverse=True)]

    def set_token(self, token):
        logging.debug('Changing token to %s', token)
        self._token = token

    def get_view_data(self, query_list, callback):
        """
        Loads multiple queries from the database, calling callback(name, series) for each one
        :param query_list: a set of query objects - either as a string of series name to load, or a tuple of series name, start date, end date
        :param callback: a function that ill be called callback(name, series) once for each series
        :return: None
        """
        queries = []
        for query_obj in query_list:
            if query_obj.start is None and query_obj.finish is None:
                queries.append(query_obj.name)
            else:
                queries.append((query_obj.name, query_obj.start, query_obj.finish))

        logging.debug('Calling getRunData with queries.')
        self._loader.getRunData(self._token, queries, callback)

    # Create a list of all instruments in simulations using the price data
    def get_instruments(self):
        instruments_obj = self._meta_obj.match({'category': 'asset'})
        instruments = sorted(instruments_obj.nodes.keys())
        return instruments

    def get_trading_sys(self):
        trading_sys = {}
        # Retrieve a list of all trading systems
        trading_obj = self._meta_obj.match({'category':'tradingsystem'})
        systems = sorted(trading_obj.group('systemName').keys())

        # Retrieve a list of sub systems under each trading system
        for sys in systems:
            subSys_obj = self._meta_obj.match({'systemName':'{}'.format(sys)})
            trading_sys[sys] = sorted(subSys_obj.group('subSystemName').keys())
        return trading_sys
