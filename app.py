import datetime
import json
import os

from operator import itemgetter

from flask import Flask
from flask import make_response
from flask import render_template
from flask import request
from gevent.pywsgi import WSGIServer
from werkzeug.contrib.cache import MemcachedCache

import local
from utils import connect_podio, get_podio, parse_podio
from utils import get_company_goals, get_marketplace_goals, get_marketplace_items

cache = MemcachedCache([os.getenv('MEMCACHE_URL', 'localhost:11211')])

app = Flask(__name__)


@app.route('/')
def home():

    results = None

    if local.ENABLE_MEMCACHE:
        results = cache.get('api_progress')

    if not results:
        # lol.  So, filters aren't documented very well in the podio
        # docs, so here's the lowdown:  You need to pass in the IDs for
        # both the keys and values here.  Values need to be in a list.
        # You can get IDs out of the API results.
        filters = {'limit': 100,
                   'sort_by': 52590680, # Phase
                   'filters': {
                               # Phase: All the phases except Concept, Define,
                               # and Complete
                               '52590680': [3,4,5,6],
                               # Status: Green, Yellow, Red
                               '52611071': [1,2,3],
                               # Team: Marketplace, Payments
                               '52603290': [3,4]
                               }
                   }
        r = get_podio(local.PODIO_PROGRESS_APPLICATION, filters)
        results = parse_podio(r)

    if local.ENABLE_MEMCACHE:
        cache.set('api_progress', results, timeout=1 * 60)

    if 'application/json' in request.headers['Accept']:
        return json.dumps({'podio': results})

    return render_template('home.html', results=results)


@app.route('/ondeck')
def ondeck():

    results = None

    if local.ENABLE_MEMCACHE:
        results = cache.get('api_ondeck')

    if not results:
        filters = {'limit': 100,
                   'filters': {
                               # Phase: Concept and Define
                               '52590680': [1,2],
                               # Status: Green, Yellow, Red. (Read: not paused)
                               '52611071': [1,2,3],
                               # Team: Marketplace, Payments
                               '52603290': [3,4]
                               }
                   }

        r = get_podio(local.PODIO_PROGRESS_APPLICATION, filters)
        results = parse_podio(r)

    if local.ENABLE_MEMCACHE:
        cache.set('api_ondeck', results, timeout=1 * 60)

    # Make sure 'Define' is there because we sort on it
    for i, item in enumerate(results):
        if not 'Define' in item:
            results[i]['Define'] = 0

    try:
        results.sort(key=itemgetter('Define'), reverse=True)
    except KeyError:
        pass

    if 'application/json' in request.headers['Accept']:
        return json.dumps({'podio': results})

    return render_template('ondeck.html', results=results)


@app.route('/scoreboard')
def scoreboard():

    results = None

    onlywaiting = request.args.get('onlywaiting','')

    if local.ENABLE_MEMCACHE:
        results = cache.get('api_scoreboard_' + onlywaiting)

    if not results:
        filters = {'limit': 150,
                   # Sort by Net Score
                   'sort_by': 53324605,
                   'filters': {
                               # Product: Marketplace, Payments, AMO
                               '53338205': [5,6,7]
                               }
                   }

        if onlywaiting:
            filters['filters']['60602479'] = [1];

        r = get_podio(local.PODIO_FEATURE_APPLICATION, filters)
        results = parse_podio(r)

    if local.ENABLE_MEMCACHE:
        cache.set('api_scoreboard_' + onlywaiting, results, timeout=1 * 60)


    # We sort on "Net Score" so we need to make sure it's there
    for i, item in enumerate(results):
        if not 'Net Score' in item:
            results[i]['Net Score'] = 0

    try:
        results.sort(key=lambda x: (x['Net Score']), reverse=True)
    except KeyError:
        pass

    return render_template('scoreboard.html', results=results)

@app.route('/testo')
def data_testo():
    return render_template('rollup.html')

@app.route('/data/rollup')
def data_rollup():

    nodes = []
    edges = []

    # You're going to love this! So, the graphing library requires the JSON to
    # be in a specific order (I know, I know, but do you want to die on that
    # hill or ship this damn thing?).  So, we build lists below, but I have to
    # know the indexes into the lists in order to draw the edges.  Voila.
    _company_goals_index = {}
    _marketplace_goals_index = {}

    # Get top level company goals
    results = get_company_goals()
    for goal in results:
        _company_goals_index[goal['Moz Objective']] = len(nodes)
        nodes.append({'name': goal['Moz Objective'], 'group': 0})

    # Get Marketplace goals
    results = get_marketplace_goals()
    for goal in results:
        _marketplace_goals_index[goal['MP Objective']] = len(nodes)
        nodes.append({'name': goal['MP Objective'], 'group': 1})

    # Get Marketplace deliverables
    results = get_marketplace_items()
    for item in results:
        if type(item['MP Objective']) is list:
            for goal in item['MP Objective']:
                try:
                    edges.append({'source':len(nodes),
                                  'target': _marketplace_goals_index[goal]})
                except KeyError:
                    pass
        else:
            try:
                edges.append({'source':len(nodes),
                              'target': _marketplace_goals_index[item['MP Objective']]})
            except KeyError:
                pass
        nodes.append({'name': item['name'], 'group': 2})


    # We can't use flask's jsonify() here because it messes with the order of
    # the JSON
    r = make_response(json.dumps({'nodes': nodes, 'links': edges}))
    r.mimetype = 'application/json'
    return r


@app.template_filter('prettydate')
def prettydate(date):
    if not date:
        return ''

    d = datetime.datetime.strptime(date, '%Y-%m-%d')
    return d.strftime('%b %d')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    ip = '0.0.0.0'
    app.debug = True
    http = WSGIServer((ip, port), app)
    print 'Listening at http://{ip}:{port}'.format(ip=ip, port=port)
    http.serve_forever()
