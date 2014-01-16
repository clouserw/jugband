import os

import json
import requests

from werkzeug.contrib.cache import MemcachedCache

cache = MemcachedCache([os.getenv('MEMCACHE_URL', 'localhost:11211')])

def calc_milestone(url):
    # TODO: handle more than github

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
