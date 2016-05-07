import os
import random
from flask import Flask, render_template, url_for, jsonify, app, request
from flask.ext.bootstrap import Bootstrap
from flask_bootstrap import WebCDN

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

bootstrap = Bootstrap(app)

# use jQuery2 instead of jQuery 1 shipped with Flask-Bootstrap
app.extensions['bootstrap']['cdns']['jquery'] = WebCDN('//cdnjs.cloudflare.com/ajax/libs/jquery/2.1.1/')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# return a json response upon request
@app.route('/rand', methods=['GET'])
def rand():
    # 't' is defined in javascript
    t = request.args.get('t', 0, type=int)
    # n here is random, but can of course be query result in a database
    n = random.random()
    return jsonify(result = n) 

if __name__ == '__main__':
    app.run(debug = True)
