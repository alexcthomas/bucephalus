import os, pdb
import argparse
import json
import sys
import traceback
import logging
import ujson
from queue import Queue
from flask import Flask, render_template, request, make_response, send_file, jsonify, Response
from flask_bootstrap import Bootstrap, WebCDN
from views.viewbuilder import ViewBuilder
from views.viewdata import ViewDataProvider
from views.viewtools import parse_tags
from views.jsonbuilder import *
from StrategyBuilder import SimLoader

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

bootstrap = Bootstrap(app)

# data_provider, view_defs = None, None

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

# return a json response upon request
@app.route('/navdata', methods=['GET'])
def get_nav_data():
    """
    Returns data for building the nav pane contents
    These won't necessarily always be static
    """
    data = []

    # Build home page
    tags = buildTags("univariate_random_bar")
    views = buildViews("basic_bar", "highcharts", tags, 1)
    page = buildPage("Root", [views])
    data.append(page)

    # Build a page of one price chart and one vol chart for each instrument
    price_names, vol_names = data_provider.get_instruments()
    # prev_price = vol_names[0]

    i, views = 0, []
    while i < len(price_names):
        item = price_names[i]

        if item.startswith("Spread"):
            i += 1
            continue

        price_tags = buildTags("price", series=item + '.prices', market=item)
        views.append(buildViews("price", "highstock", price_tags, 1))

        if i+1 < len(price_names) and item[:3] == price_names[i+1][:3]:
            # pdb.set_trace()
            i += 1
            continue


        # Find all volume data for the same instrument
        for vol_item in vol_names:
            if vol_item.startswith("Spread"):
                continue
            elif vol_item.startswith(item[:3]):
                vol_tags = buildTags("volatility", series=vol_item+'.volatility', market=vol_item.split('Position')[0])
                views.append(buildViews("volatility", "highcharts", vol_tags, 2))

        # pdb.set_trace()
        # Build the page in json
        page = buildPage(item[:3], views)
        data.append(page)
        views = []
        i += 1

    return jsonify(data)
    # return app.send_static_file(r'json/navdata.json')

# return the individual view data
@app.route('/view', methods=['GET'])
def view():
    """
    Returns a json response containing instructions for
    the javascript to render a single pane
    """
    args = dict(request.args)
    typ = args.pop('type')[0]
    argtags = args.pop('tags', [])
    tags = parse_tags(argtags)
    kwargs = {k: v[0] for k, v in args.items()}
    return view_defs.build_view(typ, tags, **kwargs)


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
                logging.debug('Partial result: %s', partial_result)
                yield(partial_result + ';')     # TODO Copies whole string - are two yield() commands better?
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bucephalus',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--port', type=int, default=5000,
        help="Web port")
    parser.add_argument('--server', type=str, default="Builder:tcp -h amazon1-stp -p 30100",
        help="URL for the StrategyBuilderServer")
    parser.add_argument('--host', type=str, default="0.0.0.0",
        help="IP address to listen on")
    params = parser.parse_args()

    global data_provider, view_defs
    data_provider = ViewDataProvider(params.server)
    view_defs = ViewBuilder(data_provider)
    app.run(debug=True, host=params.host, port=params.port)
