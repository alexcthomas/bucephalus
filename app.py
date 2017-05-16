import os, pdb
import argparse
import json
import sys
import traceback
import logging
import ujson
import PQTrading
import Psycopg2Tools
from queue import Queue
from flask import Flask, render_template, request, make_response, send_file, jsonify, Response
from flask_bootstrap import Bootstrap, WebCDN
from views.viewbuilder import ViewBuilder
from views.viewdata import ViewDataProvider
from views.jsonbuilder import *

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

bootstrap = Bootstrap(app)

# use jQuery3 instead of jQuery 1 shipped with Flask-Bootstrap
app.extensions['bootstrap']['cdns']['jquery'] = WebCDN('//cdnjs.cloudflare.com/ajax/libs/jquery/3.2.0/')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/get_tokens', methods=['GET'])
def get_tokens():
    return json.dumps(data_provider.get_tokens())

@app.route('/set_token', methods=['GET'])
def set_token():
    token = request.args.get('token')
    data_provider.set_token(token)
    return json.dumps({'token': token})

# return a json response upon request
@app.route('/navdata', methods=['GET'])
def get_nav_data():
    """
    Returns data for building the nav pane contents
    These won't necessarily always be static
    """
    data = []

    # Build a page of price charts and vol charts for each instrument
    price_names, vol_names = data_provider.get_instruments()
    i, views, all_markets= 0, [], []
    while i < len(price_names):
        item = price_names[i]

        if item.startswith("Spread"):
            i += 1
            continue

        all_markets.append(item)
        price_tag = buildTags("price", series=item + '.prices', market=item)
        views.append(buildViews("price", price_tag, 1))

        if i+1 < len(price_names) and item[:3] == price_names[i+1][:3]:
            i += 1
            continue

        # Find all volume data for the same instrument
        for vol_item in vol_names:
            if vol_item.startswith("Spread"):
                continue
            elif vol_item.startswith(item[:3]):
                vol_tag = buildTags("volatility", series=vol_item+'.volatility', market=vol_item.split('Position')[0])
                views.append(buildViews("volatility", vol_tag, 2))

        # Build the page in json
        page = buildPage(PQTrading.instrumentToLongName[item[:3]], views)
        data.append(page)
        views = []
        i += 1

    # Build home page with multiple graphs
    # Build PnL graph
    home_view = []
    row = 1
    portf_tag = buildTags("price", series='Portfolio.netPL, Portfolio.grossPL', market='Net P&L')
    home_view.append(buildViews("accumulated", portf_tag, 1))
    row += 1

    # Build correlation table
    # all_markets = ["ADCC1", "ALMC1", "FTEC1", "SSEC3"]
    all_series = ', '.join([n + '.prices' for n in all_markets])
    correl_tag = buildTags("price", series=all_series, market='All Markets', axis=all_markets)
    home_view.append(buildViews("correlation", correl_tag, 2))
    row += 1

    # Build histogram graph
    histo_tag = buildTags("price", series="Portfolio.netPL", market="Annual Net Portf")
    home_view.append(buildViews("histogram", histo_tag, 3))

    home_page = buildPage("Root", home_view)
    data.append(home_page)
    logging.debug("json %s", data)

    return jsonify(data)


@app.route('/views', methods=['POST'])
def views():
    result_queue = Queue()

    # This function does not block until the results are all back
    worker_thread = view_defs.build_views(request.json, result_queue)

    # Flask can send results back piecemeal, but it needs a generator to do this.  We block on the callback
    # here by waiting on the result_queue.
    def result_generator():
        try:
            while True:
                result = result_queue.get(block=True)
                if not result:
                    break
                partial_result = ujson.dumps(result)
                yield(partial_result)
                yield(';')
            logging.debug('Waiting for worker thread')
            worker_thread.join()
            logging.debug('Call completed')
        except Exception:
            ex_type, ex, tb = sys.exc_info()
            logging.error('Error in result_generator: {}\n{}'.format(ex, "\n".join(traceback.format_tb(tb))))

    return app.response_class(result_generator(), mimetype='text/plain')


@app.route("/img/<path:path>")
def images(path):
    """
    Returns an image, if created by a view.
    """
    fullpath = "./img/" + path
    resp = make_response(open(fullpath, 'rb').read())
    resp.content_type = "image/jpeg"
    return resp


class LoadFromFile(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        with values as f:
            contents = f.read()
            data = parser.parse_args(contents.split())
            for k, v in vars(data).items():
                if v and k != option_string.lstrip('-'):
                    setattr(namespace, k, v)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bucephalus',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--port', type=int, default=5000,
        help="Web port")
    parser.add_argument('--config', type=open, default='app.config',
        help='Configuration file to load')
    parser.add_argument('--server', type=str, action=LoadFromFile, default="Builder:tcp -h amazon1-stp -p 30100",
        help="URL for the StrategyBuilderServer")
    parser.add_argument('--dbhost', type=str, default="amazon1-postgres",
        help="Database hostname")
    parser.add_argument('--dbname', type=str, default="marketdata",
        help="Database name")
    parser.add_argument('--dbport', type=int, default=5440,
        help="Database port")
    parser.add_argument('--dbuser', type=str, default="readonly",
        help="Database user")
    parser.add_argument('--dbpassword', type=str, default="readonly",
        help="Database password")
    parser.add_argument('--host', type=str, default="0.0.0.0",
        help="IP address to listen on")
    params = parser.parse_args()

    global data_provider, view_defs
    factory = Psycopg2Tools.ConnectionFactory(params.dbhost, params.dbname, params.dbuser,
        params.dbpassword, params.dbport)
    PQTrading.populateStaticData(factory)
    data_provider = ViewDataProvider(params.server, factory)
    view_defs = ViewBuilder(data_provider)
    app.run(debug=True, host=params.host, port=params.port)
