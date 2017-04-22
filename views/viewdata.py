import numpy as np, pdb
import pandas as pd
from viewtools import encode_series, encode_pandas_series

class ViewDataProvider(object):
    """
    This class maps from tags to datasets
    Could be e.g. from a database
    """

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












