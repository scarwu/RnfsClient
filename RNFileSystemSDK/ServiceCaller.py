#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib

'''
REST Service API Caller
'''
class ServiceCaller():
    def __init__(self, server, port, ssl):
        self.server = server
        self.port = port
        self.ssl = ssl
    
    '''
    Send Request
    '''
    def send(self, config):
        # Connection with HTTP or HTTPS
        if self.ssl:
            conn = httplib.HTTPSConnection(self.server, self.port)
        else:
            conn = httplib.HTTPConnection(self.server, self.port)
        
        # Url
        url = "/" + config['api']
        
        if config['path'] != None:
            url += "/" + config['path']
        
        # Parameter
        if str.lower(config['method']) == 'get':
            params = None
            if config['params'] != None:
                url += "?" + config['params']
        else:
            params = config['params']
        
        # Send Request
        conn.request(str.upper(config['method']), url, params, config['headers'])
        response = conn.getresponse()
        result = {
            "status": response.status,
            "reason": response.reason,
            "data": response.read()
        }
        conn.close()
        return result