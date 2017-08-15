import uuid
import logging
import datetime

import numpy as np
import pandas as pd

from views.viewtools import encode_series, encode_pandas_series


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

    def get_view_data(self, tags, **kwargs):

        typ = tags.pop('datatype', None)

        # Some views don't need data
        if typ is None:
            return

        if typ == "solar":
            ret = [{
                        'name': 'Installation',
                        'data': [43934, 52503, 57177, 69658, 97031, 119931, 137133, 154175]
                    }, {
                        'name': 'Manufacturing',
                        'data': [24916, 24064, 29742, 29851, 32490, 30282, 38121, 40434]
                    }, {
                        'name': 'Sales & Distribution',
                        'data': [11744, 17722, 16005, 19771, 20185, 24377, 32147, 39387]
                    }, {
                        'name': 'Project Development',
                        'data': [None, None, 7988, 12169, 15112, 22452, 34400, 34227]
                    }, {
                        'name': 'Other',
                        'data': [12908, 5948, 8105, 11248, 8989, 11816, 18274, 18111]
                    }]
            return ret

        if typ == "population":
            ret = [{
                        'name': 'Year 1800',
                        'data': [107, 31, 635, 203, 2]
                    }, {
                        'name': 'Year 1900',
                        'data': [133, 156, 947, 408, 6]
                    }, {
                        'name': 'Year 2012',
                        'data': [1052, 954, 4250, 740, 38]
                    }]
            return ret

        if typ == "univariate_random":
            return np.random.randn(200)

        if typ == "univariate_random_bar":
            ret = [{
                        'name': 'Random',
                        'data': np.random.randn(100)
                    }]
            return ret

        if typ == "random_timeseries":
            data = np.cumsum(np.random.randn(2000))
            dates = pd.bdate_range('2000-01-01', periods=2000, freq='B')
            ret = [{
                        'name': 'Random',
                        'data': encode_series(dates, data)
                    }]
            return ret

        if typ == "random_vol":
            vals = np.random.randn(2000)
            dates = pd.bdate_range('2000-01-01', periods=2000, freq='B')
            ts = pd.Series(np.sqrt(pd.ewma(vals*vals,span=5)), dates)
            ret = [{
                        'name': 'Random',
                        'data': encode_pandas_series(ts)
                    }]
            return ret

        raise RuntimeError('No data found for type {}'.format(typ))












