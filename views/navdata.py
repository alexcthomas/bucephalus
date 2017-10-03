import logging

import json

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)


def build_pages(data_provider):
    """
    Build JSON pages for the entire website
    """

    return json.load(open(r'static/json/navdata.json', 'r'))





