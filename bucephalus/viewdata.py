import time
import logging
import datetime

from StrategyBuilder import SimLoader

import PQTrading
import Psycopg2Tools


class ViewDataProvider(object):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    """
    This class maps from tags to datasets
    Could be e.g. from a database
    """
    def __init__(self, config):
        logging.info("Connecting to {}".format(config['SIMSERVER']))
        self._loader = SimLoader(config['SIMSERVER'])
        logging.info("Building factory")
        self._factory = Psycopg2Tools.ConnectionFactory(config['DBHOST'],
                                                        config['DBNAME'],
                                                        config['DBUSER'],
                                                        config['DBPASSWORD'],
                                                        config['DBPORT'])

        logging.info("Getting static data")
        PQTrading.populateStaticData(self._factory)

    def get_tokens(self):
        tokens = self._loader.getRunTokens(datetime.datetime(1990, 1, 1), datetime.datetime.utcnow())
        return [t[0] for t in sorted(tokens, key=lambda x: x[1], reverse=True) if t[0].startswith('[Taurus')][:10]

    def get_view_data(self, token, query_list, callback):
        """
        Loads multiple queries from the database, calling callback(name, series) for each one
        :param query_list: a set of query objects - a string of series name to load,
        :param callback: a function that will be called as callback(name, series) once for each series
        :return: None
        """
        queries = [q[0] for q in query_list]
        logging.debug('Calling getRunData with {} queries.'.format(len(queries)))
        t0 = time.time()
        self._loader.getRunArray(token, queries, callback)
        logging.debug('getRunArray took {}s'.format(time.time()-t0))


