import os
import json
import logging

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)


def build_pages(data_provider):
    """
    Build JSON pages for the entire website
    """

    modpath = os.path.dirname(__file__)
    datapath = os.path.join(modpath, 'static', 'json', 'navdata.json')
    return json.load(open(datapath, 'r'))





