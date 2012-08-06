#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib
import urllib2

conn = httplib.HTTPConnection('127.0.0.1', 80)

conn.request('POST', urllib2.quote('/file/sffd sdfsdf'), None)

response = conn.getresponse()

print response.read()
print response.status

conn.close()