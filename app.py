import os

from flask import Flask
from flask import render_template
from flask import request
from gevent.pywsgi import WSGIServer
from werkzeug.contrib.cache import MemcachedCache

import local
from utils import calc_milestone, connect_podio, parse_podio

cache = MemcachedCache([os.getenv('MEMCACHE_URL', 'localhost:11211')])

app = Flask(__name__)


@app.route('/')
def home():

    r = cache.get('api_progress')
    if not r:
        c = connect_podio()
        # lol.  So, filters aren't documented very well in the podio
        # docs, so here's the lowdown:  You need to pass in the IDs for
        # both the keys and values here.  Values need to be in a list.
        # You can get IDs out of the API results.
        r = c.Item.filter(local.PODIO_PROGRESS_APPLICATION,
                          {'limit': 50,
                           'filters': {
                               # Phase
                               '52590680': [1,2,3,4,5,6,8],
                               # Status
                               '52611071': [1,2,3]}
                          })
    cache.set('api_progress', r, timeout=2 * 60)

    # @TODO result too big for memcache
    results = parse_podio(r, extrasauce=request.args.get('extrasauce'))

    try:
        results.sort(key=lambda x: (x['Phase']), reverse=True)
    except KeyError:
        pass

    return render_template('home.html', results=results)


@app.route('/scoreboard')
def scoreboard():

    r = cache.get('api_scoreboard')
    if not r:
        c = connect_podio()
        r = c.Item.filter(local.PODIO_FEATURE_APPLICATION, {'limit': 50})
        cache.set('api_scoreboard', r, timeout=2 * 60)

    results = parse_podio(r, extrasauce=request.args.get('extrasauce'))

    # We sort on "Net Score" so we need to make sure it's there
    for i, item in enumerate(results):
        if not 'Net Score' in item:
            results[i]['Net Score'] = 0

    try:
        results.sort(key=lambda x: (x['Net Score']), reverse=True)
    except KeyError:
        pass

    return render_template('scoreboard.html', results=results)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    ip = '0.0.0.0'
    #app.debug = True
    http = WSGIServer((ip, port), app)
    print 'Listening at http://{ip}:{port}'.format(ip=ip, port=port)
    http.serve_forever()
