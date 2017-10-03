import os, pdb
import sys
import json
import ujson
import logging
import argparse
import traceback
import datetime as dt
from queue import Queue

import numpy as np

from flask import Flask, render_template, request, jsonify, send_file
from flask_bootstrap import Bootstrap, WebCDN

from views.viewbuilder import ViewBuilder
from views.viewdata import ViewDataProvider
from views.navdata import build_pages

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config.from_json('app.config')

data_provider = ViewDataProvider(app.config)
view_defs = ViewBuilder(data_provider)

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
    return render_template('index.html', tokens=data_provider.get_tokens())


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
    """
    data = build_pages(data_provider)
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

                # Convert NaN's to 0's
                if 'data' == result['category'] and result['data'] is not None:
                    for data in result['data']:
                        # Portfolio PnL breakdown's data is in the form of dictionary,
                        # hence can't use np.isnan to check for NaN's
                        if type(data) is not dict and np.isnan(data[1]):
                            data[1] = 0

                partial_result = ujson.dumps(result)
                yield(partial_result.encode('utf-8'))
                yield(';'.encode('utf-8'))

            logging.debug('Waiting for worker thread')
            worker_thread.join()
            logging.debug('Call completed')
        except Exception:
            ex_type, ex, tb = sys.exc_info()
            logging.error('Error in result_generator: {}\n{}'.format(ex, "\n".join(traceback.format_tb(tb))))

    return app.response_class(result_generator(), mimetype='text/plain', direct_passthrough=True)


@app.route("/img/<path:path>")
def images(path):
    """
    Returns an image, if created by a view.
    """
    fullpath = "./img/" + path
    return send_file(fullpath, mimetype='image/png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bucephalus',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--port', type=int, default=5000,
        help="Web port")
    parser.add_argument('--host', type=str, default="0.0.0.0",
        help="IP address to listen on")
    params = parser.parse_args()

    app.run(debug=True, host=params.host, port=params.port, threaded=True)









