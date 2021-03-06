import datetime
import json
import os

from operator import itemgetter

from flask import Flask
from flask import render_template
from flask import request
from gevent.pywsgi import WSGIServer
from werkzeug.contrib.cache import MemcachedCache

import local
from utils import connect_podio, get_podio, parse_podio

cache = MemcachedCache([os.getenv('MEMCACHE_URL', 'localhost:11211')])

app = Flask(__name__)


@app.route('/')
def home():

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
                           # Roadmap Status: Active
                           '86551352': [2],
                           # Team: Marketplace
                           '52603290': [3]
                           }
               }
    r = get_podio(local.PODIO_PROGRESS_APPLICATION, filters)
    results = parse_podio(r)

    if 'application/json' in request.headers['Accept']:
        return json.dumps({'podio': results})

    return render_template('home.html', results=results)


@app.route('/ondeck')
def ondeck():

    filters = {'limit': 100,
               'filters': {
                           # Roadmap Status: Active
                           '86551352': [2],
                           # Phase: Concept and Define
                           '52590680': [1,2],
                           # Team: Marketplace
                           '52603290': [3]
                           }
               }

    r = get_podio(local.PODIO_PROGRESS_APPLICATION, filters)
    results = parse_podio(r)

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


@app.route('/roadmap')
def roadmap():

    filters = {'limit': 150,
               'filters': {
                           # Phase: Everything except Cancelled and Complete
                           '52590680': [1,2,3,4,5,6],
                           # Team: Marketplace
                           '52603290': [3]
                           }
               }

    r = get_podio(local.PODIO_PROGRESS_APPLICATION, filters)
    results = parse_podio(r)

    # Make sure 'Define' is there because we sort on it
    for i, item in enumerate(results):
        if not 'Target Launch_end' in item:
            results[i]['Target Launch_end'] = 0

    try:
        results.sort(key=itemgetter('Target Launch_end'))
    except KeyError:
        pass

    if 'application/json' in request.headers['Accept']:
        return json.dumps({'podio': results})

    return render_template('roadmap.html', results=results)


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
