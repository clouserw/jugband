import os

from flask import Flask
from flask import render_template
from flask import request
from gevent.pywsgi import WSGIServer
from pypodio2 import api as podio

import local

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

            if f['type'] == 'progress':
                o[f['label']] = f['values'][0]['value']

            if f['type'] == 'embed':
                o[f['label']] = f['values'][0]['embed']['url']

        results.append(o)

    results.sort(key=lambda x: (x['status'],x['priority'],x['name']))

    return render_template('home.html', results=results)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    ip = '0.0.0.0'
    http = WSGIServer((ip, port), app)
    print 'Listening at http://{ip}:{port}'.format(ip=ip, port=port)
    http.serve_forever()
