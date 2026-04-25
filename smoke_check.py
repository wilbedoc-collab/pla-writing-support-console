#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import urllib.request

URLS = [
    'http://127.0.0.1:8765/api/session',
    'http://127.0.0.1:8765/api/document/deepevidence-v1/overview',
    'http://127.0.0.1:8765/api/document/deepevidence-v1/sentences',
    'http://127.0.0.1:8765/api/document/deepevidence-v1/sentence/S003',
    'http://127.0.0.1:8765/api/document/deepevidence-v1/sentence/S003/evidence',
    'http://127.0.0.1:8765/api/document/deepevidence-v1/sentence/S003/suggestions',
    'http://127.0.0.1:8765/api/document/deepevidence-v1/sentence/S003/refutation',
    'http://127.0.0.1:8765/api/document/deepevidence-v1/pending-fulltext',
    'http://127.0.0.1:8765/api/document/deepevidence-v1/alerts',
]

for url in URLS:
    with urllib.request.urlopen(url) as r:
        obj = json.load(r)
    if isinstance(obj, dict):
        preview = list(obj.keys())[:6]
    else:
        preview = str(type(obj))
    print(url, 'OK', preview)
