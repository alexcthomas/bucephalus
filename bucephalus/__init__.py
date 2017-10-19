import os
import sys
import json
import logging
from queue import Queue

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory

from .viewbuilder import ViewBuilder
from .viewdata import ViewDataProvider
from .navdata import build_pages
from .viewtools import to_json, build_json_msg, build_error, build_error_message

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config.from_json('../app.config')

data_provider = ViewDataProvider(app.config)
view_defs = ViewBuilder(data_provider)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/', methods=['GET'])
def index():
    return send_from_directory('static', 'index.html')


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

    try:
        result_queue = Queue()

        # This function does not block until the results are all back
        worker_thread = view_defs.build_views(request.json, result_queue)

    except Exception:
        msg = build_error_message('There was an error building the page views:')
        logging.error(msg)
        result = (build_json_msg(build_error(msg)), )
        return app.response_class(result, mimetype='application/json', direct_passthrough=True)

    # Flask can send results back piecemeal, but it needs a generator to do this.
    # We block on the callback here by waiting on the result_queue.
    def result_generator():
        while True:
            result = result_queue.get(block=True)

            # finished the queue
            if result is None:
                break

            partial_result = to_json(result)+';'
            yield(partial_result.encode('utf-8'))

        logging.debug('Waiting for worker thread')
        worker_thread.join()
        logging.debug('Call completed')

    return app.response_class(result_generator(), mimetype='application/json', direct_passthrough=True)


@app.route("/img/<path:path>")
def images(path):
    """
    Returns an image, if created by a view.
    """
    fullpath = "./img/" + path
    return send_file(open(fullpath, 'rb'), mimetype='image/png')
