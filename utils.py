import os

import json
import requests

from pypodio2 import api as podio
from werkzeug.contrib.cache import MemcachedCache

import local

cache = MemcachedCache([os.getenv('MEMCACHE_URL', 'localhost:11211')])


def calc_milestone(url):
    # TODO: handle more than github
    # TODO: This is broken right now.  Miscalculating somehow

    c = cache.get(url)

    if not c:
        r = requests.get(url)
        if r.ok:
            try:
                c = r.json()
                cache.set(url, c, timeout=2 * 60)
            except requests.exceptions.RequestException as e:
                c = None

    try:
        ret = "%.0f" % ((float(c['closed_issues']) /
                         float(c['open_issues'])) * 100)
    except:
        ret = 0
        pass

    return ret


def connect_podio():
    c = podio.OAuthClient(local.PODIO_CLIENT_ID,
                          local.PODIO_CLIENT_SECRET,
                          local.PODIO_USER,
                          local.PODIO_PASS)
    return c

def get_podio(app, filters=None):
    c = connect_podio()
    r = c.Item.filter(app, filters)
    return r


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

