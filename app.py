import os, pdb
from flask import Flask, render_template, request, make_response, send_file
from flask_bootstrap import Bootstrap, WebCDN
from views.viewbuilder import ViewBuilder
from views.viewdata import ViewDataProvider
from views.viewtools import parse_tags

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

bootstrap = Bootstrap(app)

data_provider = ViewDataProvider()
view_defs = ViewBuilder(data_provider)

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

# return a json response upon request
@app.route('/navdata', methods=['GET'])
def get_nav_data():
    """
    Returns data for building the nav pane contents
    These won't necessarily always be static
    """
    return app.send_static_file(r'json/navdata.json')

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
    kwargs = {k:v[0] for k,v in args.items()}
    return view_defs.build_view(typ, tags, **kwargs)

@app.route("/img/<path:path>")
def images(path):
    """
    Returns an image, if created by a view.
    """
    fullpath = "./img/" + path
    return send_file(fullpath, mimetype='image/png')

def reload_views_provider(path):
    """For reloading the views"""
    view_defs.reload_views()

def reload_data_provider(path):
    """
    For reloading the data provider
    e.g. switching database
    """
    global data_provider
    data_provider = ViewDataProvider()
    view_defs.set_data_provider(data_provider)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
