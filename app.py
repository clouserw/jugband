import os

from flask import Flask
from flask import render_template
from flask import request
from gevent.pywsgi import WSGIServer
from pypodio2 import api as podio
from werkzeug.contrib.cache import MemcachedCache

import local
from utils import calc_milestone

cache = MemcachedCache([os.getenv('MEMCACHE_URL', 'localhost:11211')])

app = Flask(__name__)


@app.route('/')
def home():

    c = podio.OAuthClient(local.PODIO_CLIENT_ID,
                          local.PODIO_CLIENT_SECRET,
                          local.PODIO_USER,
                          local.PODIO_PASS)

    r = c.Application.get_items(local.PODIO_APPLICATION)

    results = []

    for i in r['items']:
        o = {}

        if request.args.get('extrasauce'):
            o['podio_link'] = i['link']

        for f in i['fields']:

            if f['type'] == 'text':
                o[f['label']] = f['values'][0]['value']

            if f['type'] == 'category':
                o[f['label']] = f['values'][0]['value']['text']

            if f['type'] == 'category' and len(f['values']) > 1:

                o[f['label']] = []

                for v in f['values']:
                    o[f['label']].append(v['value']['text'])

            if f['type'] == 'progress':
                o[f['label']] = f['values'][0]['value']

            if f['label'] == 'milestone_override':
                o['dev_complete'] = calc_milestone(o['milestone_override'])

            if f['type'] == 'embed':
                o[f['label']] = f['values'][0]['embed']['url']

        results.append(o)

    try:
        results.sort(key=lambda x: (x['status'],x['priority'],x['name']))
    except KeyError:
        pass



    return render_template('home.html', results=results)

@app.route('/scoreboard')
def scoreboard():

    # TODO: make this a function!
    c = podio.OAuthClient(local.PODIO_CLIENT_ID,
                          local.PODIO_CLIENT_SECRET,
                          local.PODIO_USER,
                          local.PODIO_PASS)

    # TODO: this shouldn't be hardcoded, heh
    # No filtering here yet...maybe we'll need that some day?
    r = c.Application.get_items(6867369)

    results = []

    for i in r['items']:
        o = {}

        if request.args.get('extrasauce'):
            o['podio_link'] = i['link']

        # set a default because we sort on it
        o['Net Score'] = 0

        # TODO: this whole thing should be a function to share with home()
        for f in i['fields']:

            if f['type'] == 'text':
                o[f['label']] = f['values'][0]['value']

            if f['type'] == 'category':
                o[f['label']] = f['values'][0]['value']['text']

            if f['type'] == 'category' and len(f['values']) > 1:

                o[f['label']] = []

                for v in f['values']:
                    o[f['label']].append(v['value']['text'])

            if f['type'] == 'progress':
                o[f['label']] = f['values'][0]['value']

            if f['label'] == 'milestone_override':
                o['dev_complete'] = calc_milestone(o['milestone_override'])

            if f['type'] == 'embed':
                o[f['label']] = f['values'][0]['embed']['url']

            if f['type'] == 'number':
                o[f['label']] = int(float(f['values'][0]['value']))

        results.append(o)

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
