import os
import ujson
import logging
from queue import Queue

from flask import Flask, request, send_from_directory, jsonify

from .viewbuilder import ViewBuilder
from .viewdata import ViewDataProvider
from .navdata import build_pages
from .viewtools import to_json, build_json_msg, build_error, build_error_message

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config.from_json('../app.config')

data_provider = ViewDataProvider(app.config)
view_defs = ViewBuilder(data_provider)


@app.route('/get_tokens', methods=['GET'])
def get_tokens():
    """
    Returns a list of data source connection tokens
    """
    result = (ujson.dumps(data_provider.get_tokens()), )
    return app.response_class(result, mimetype='application/json')


# return a json response upon request
@app.route('/navdata/<token>', methods=['GET'])
def get_nav_data(token):
    """
    Returns data for building the nav pane contents
    """
    data = build_pages(data_provider, token)
    return jsonify(data)


@app.route('/views/<token>', methods=['POST'])
def views(token):

    try:
        result_queue = Queue()

        # This function does not block until the results are all back
        worker_thread = view_defs.build_views(token, request.json, result_queue)

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


###################################
#
# The following functions should only be
# called when using a development server
#
###################################


@app.route('/', methods=['GET'])
def index():
    """
    Index page
    """
    return send_from_directory('static', 'index.html')


@app.route("/img/<path:path>")
def images(path):
    """
    Returns an image, if created by a view.
    """
    return send_from_directory('../img', path, mimetype='image/png')
