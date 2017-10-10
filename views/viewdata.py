import logging
import datetime

from views.viewtools import level_value_string_sub

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

        logging.info("Getting tokens")
        # Default to the latest token retrieved
        token = self.get_tokens()[0]

        logging.info("Setting tokens")
        self.set_token(token)

    def get_tokens(self):
        tokens = self._loader.getRunTokens(datetime.datetime(1990, 1, 1), datetime.datetime.utcnow())
        return [t[0] for t in sorted(tokens, key=lambda x: x[1], reverse=True) if t[0].startswith('[Taurus')][:10]

    def set_token(self, token):
        logging.debug('Setting token to %s', token)
        self._token = token
        self._meta_obj = self._loader.getRunMeta(self._token)

    def get_view_data(self, query_list, callback):
        """
        Loads multiple queries from the database, calling callback(name, series) for each one
        :param query_list: a set of query objects - a string of series name to load,
        :param callback: a function that will be called as callback(name, series) once for each series
        :return: None
        """
        queries = [q[0] for q in query_list]
        logging.debug('Calling getRunData with {} queries.'.format(len(queries)))
        self._loader.getRunData(self._token, queries, callback)

    def get_series_key_from_tags(self, tags, series_label):
        """
        For a set of sim objects specified by a a category, a sim class, and a set of tags
        Get the given output series
        """
        output_name = tags.pop('output')
        obj_name = list(self._meta_obj.match(tags).nodes.keys())[0]
        this_series_label = level_value_string_sub(series_label, tags)
        query = '.'.join([obj_name, output_name])
        return query, obj_name, this_series_label
