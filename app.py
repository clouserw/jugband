import datetime
import json
import os

from flask import Flask
from flask import render_template
from flask import request
from gevent.pywsgi import WSGIServer
from werkzeug.contrib.cache import MemcachedCache

import local
from utils import calc_milestone, connect_podio, get_podio, parse_podio

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
                               # Phase: All the phases except Complete
                               '52590680': [1,2,3,4,5,6],
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
        # Right now this is the exact same query as home().  That means we could
        # just use that cached value from memcache and save ourselves the
        # roundtrip.  However, I'd like to let this bake for a bit before I take
        # that code out as this stuff seems to change a lot still.
        filters = {'limit': 100,
                   'sort_by': 52590680, # Phase
                   'filters': {
                               # Phase: All the phases except Complete
                               '52590680': [1,2,3,4,5,6],
                               # Status: Green, Yellow, Red
                               '52611071': [1,2,3],
                               # Team: Marketplace, Payments
                               '52603290': [3,4]
                               }
                   }

        r = get_podio(local.PODIO_PROGRESS_APPLICATION, filters)
        results = parse_podio(r)

    if local.ENABLE_MEMCACHE:
        cache.set('api_ondeck', results, timeout=1 * 60)

    try:
        results.sort(key=lambda x: (x['Priority']), reverse=False)
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

@app.template_filter('prettydate')
def prettydate(date):
    if not date:
        return ''

    d = datetime.datetime.strptime(date, '%Y-%m-%d')
    return d.strftime('%b %d')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    ip = '0.0.0.0'
    #app.debug = True
    http = WSGIServer((ip, port), app)
    print 'Listening at http://{ip}:{port}'.format(ip=ip, port=port)
    http.serve_forever()
