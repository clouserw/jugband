import os

import hashlib
import json
import requests

from pypodio2 import api as podio
from werkzeug.contrib.cache import MemcachedCache

import local

cache = MemcachedCache([os.getenv('MEMCACHE_URL', 'localhost:11211')])

def connect_podio():
    c = podio.OAuthClient(local.PODIO_CLIENT_ID,
                          local.PODIO_CLIENT_SECRET,
                          local.PODIO_USER,
                          local.PODIO_PASS)
    return c

def get_podio(app, filters=None):

    results = None

    if local.ENABLE_MEMCACHE:
        _key = hashlib.md5(str(app) + json.dumps(filters))
        results = cache.get(_key.hexdigest())

    if not results:
        c = connect_podio()
        results = c.Item.filter(app, filters)

    if local.ENABLE_MEMCACHE:
        cache.set(_key.hexdigest(), results, timeout=local.MEMCACHE_TIMEOUT)

    return results


def parse_podio(juicydata):
    """This converts the awesome-yet-very-verbose podio API output into
    something that is easier to use in our templates.
    """
    results = []

    for i in juicydata['items']:
        o = {}

        o['name'] = i['title']

        o['podio_link'] = i['link']

        for f in i['fields']:

            # Currently only retrieving the titles for linked apps
            if f['type'] == 'app':
                o[f['label']] = f['values'][0]['value']['title']

            if f['type'] == 'app' and len (f['values']) > 1:
                o[f['label']] = []

                for v in f['values']:
                    o[f['label']].append(v['value']['title'])

            if f['type'] == 'date':
                o[f['label']] = f['values'][0]['start_date']

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

            if f['type'] == 'embed':
                o[f['label']] = f['values'][0]['embed']['url']

            if f['type'] == 'number':
                o[f['label']] = int(float(f['values'][0]['value']))

        results.append(o)

    return results

