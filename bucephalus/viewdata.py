import uuid
import logging

import numpy as np
import pandas as pd

from bucephalus.viewtools import level_value_string_sub, encode_pandas_series, encode_series


class ViewDataProvider(object):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    """
    This class maps from tags to datasets

    Connection settings can be modified by changing the "token"
    which could be e.g. a db schema/instance or computation output
    """

    def __init__(self, config):
        logging.info("Initialising ViewDataProvider with config:".format(config))

        # Default to the latest token retrieved
        self.set_token(self.get_tokens()[0])

    def get_tokens(self):
        """
        Return the list of valid tokens
        Use random uuids for example values
        """
        tokens = [str(uuid.uuid4()) for _ in range(10)]
        return sorted(tokens)

    def set_token(self, token):
        """
        Sets the data connection token to the one given
        Then performs any connecting/reloading necessary.
        """
        logging.debug('Setting token to %s', token)
        # TODO - validate token
        self._token = token

        # Reload the db connection here
        # connection.reload()

    def get_single_query_data(self, query):

        # Some views don't need data
        if query is None or not query:
            # TODO - in that case, why are we even here?
            return

        parts = query.split('.')
        typ = parts[0]

        if typ == "solar":
            data = {'installation':  [43934, 52503, 57177, 69658, 97031, 119931, 137133, 154175],
                    'manufacturing': [24916, 24064, 29742, 29851, 32490, 30282, 38121, 40434],
                    'sales':         [11744, 17722, 16005, 19771, 20185, 24377, 32147, 39387],
                    'development':   [None, None, 7988, 12169, 15112, 22452, 34400, 34227],
                    'other':         [12908, 5948, 8105, 11248, 8989, 11816, 18274, 18111]
                    }
            return pd.Series(data[parts[1]])

        if typ == "population":
            data = {'1800': [107, 31, 635, 203, 2],
                    '1900': [133, 156, 947, 408, 6],
                    '2012': [1052, 954, 4250, 740, 38],
                    }
            return pd.Series(data[parts[1]])

        if typ == "univariate_random":
            return pd.Series(np.random.randn(200))

        if typ == "random_timeseries":
            data = np.random.randn(2000)
            dates = pd.bdate_range('2000-01-01', periods=2000, freq='B')
            return encode_series(dates, data)

        if typ == "random_vol":
            vals = np.random.randn(2000)
            dates = pd.bdate_range('2000-01-01', periods=2000, freq='B')
            data = np.sqrt(pd.ewma(vals*vals, span=5))
            return encode_series(dates, data)

        raise RuntimeError('No data found for type {}'.format(query))

    def get_view_data(self, token, query_list, callback):
        """
        Loads multiple queries from the database, calling callback(name, series) for each one
        :param query_list: a set of query objects - a string of series name to load,
        :param callback: a function that will be called as callback(name, series, i, n) once for each series
        :return: None
        """
        n_queries = len(query_list)
        logging.debug('Getting data for {} queries.'.format(n_queries))

        # This call we should really be making is this one:
#        self.connection.run_queries([q[0] for q in query_list], callback)

        # But for this example, we'll just iterate through the queries
        # invoking the callback as we go
        for i, q in enumerate(query_list):
            data = self.get_single_query_data(q[0])
            callback(q[0], data, i+1, n_queries)
