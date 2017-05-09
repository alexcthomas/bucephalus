import numpy as np, pdb
import pandas as pd
import datetime
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
    def __init__(self, server):
        logging.info("Connecting to {}".format(server))
        self._loader = SimLoader(server)

        # Default to the latest token retrieved
        # self._token = self.get_tokens()[0]

        # Use the token with volatility data
        self._token = '[Parallelism.Pegasus-NoCross:20170504T100847.816352,1]'

    def get_tokens(self):
        tokens = self._loader.getRunTokens(datetime.datetime(1990, 1, 1), datetime.datetime.utcnow())
        return [t[0] for t in sorted(tokens, key=lambda x: x[1], reverse=True)]

    def set_token(self, token):
        self._token = token

    def get_view_data(self, tags, **kwargs):
        typ = tags.pop('datatype', None)

        # Some views don't need data
        if typ is None:
            return

        if typ == "univariate_random_bar":
            ret = [{
                        'name': 'Random',
                        'data': np.random.randn(100)
                    }]
            return ret

        if typ in ['series']: # 'price', 'volatility',
            # series = [s.strip(' ') for s in names.split(',')]
            # series = [s.strip(' ') for s in tags.pop('series', []).split(',')]
            series = tags.pop('series')
            series = series if isinstance(series, list) else [series]
            logging.debug('Query for series: %s', " and ".join(series))

            data = self._loader.getRunData(self._token, series)
            logging.debug('Data loader - post-processing')
            results = []
            for k, v in data.items():
                dates, value = zip(*v)
                s = pd.Series(value, index=dates)
                results.append({'name': k, 'data': encode_pandas_series(s)})
            logging.debug('Returning results')
            return results

        raise RuntimeError('No data found for type {}'.format(typ))

    # Create a list of all instruments in simulations using the price data
    def get_instruments(self):
        meta_obj = self._loader.getRunMeta(self._token)
        price_obj = meta_obj.match({'category': 'asset'})
        vol_obj = meta_obj.match({'category': 'volatility'})

        price_keys = sorted(price_obj.nodes.keys())
        vol_keys = sorted(vol_obj.nodes.keys())
        # pdb.set_trace()
        return price_keys, vol_keys