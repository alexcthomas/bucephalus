import os, pdb
import sys
import json
import ujson
import logging
import traceback
import datetime as dt
from queue import Queue

import numpy as np

from flask import Flask, render_template, request, jsonify, send_file
from flask_bootstrap import Bootstrap, WebCDN

from .viewbuilder import ViewBuilder
from .viewdata import ViewDataProvider
from .navdata import build_pages

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config.from_json('../app.config')

print('Starting data provider')
data_provider = ViewDataProvider(app.config)

print('Starting view builder')
view_defs = ViewBuilder(data_provider)

print('Building bootstrap')
bootstrap = Bootstrap(app)

print('Starting app')

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

    # Flask can send results back piecemeal, but it needs a generator to do this.
    # We block on the callback here by waiting on the result_queue.
    def result_generator():
        try:
            while True:
                result = result_queue.get(block=True)

                if result is None:
                    break

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
    print(os.path.realpath(fullpath))
    return send_file(open(fullpath, 'rb'), mimetype='image/png')
