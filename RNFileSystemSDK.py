#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib
import json

class RNFileSystemSDK():
    def __init__(self, username, password, server, port, ssl):
        self.username = username
        self.password = password
        self.server = server
        self.port = port
        self.ssl = ssl    
    
    def _send(self, config):
        # Connection with HTTP or HTTPS
        if self.ssl:
            conn = httplib.HTTPSConnection(self.server, self.port)
        else:
            conn = httplib.HTTPConnection(self.server, self.port)
        
        # URL
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
    
    '''
    Json Encoder
    '''
    def __encode(self, data):
        return json.dumps(data, separators=(',', ':'))
    
    def getResult(self):
        return self.result
    
    '''
    Authentication API
    '''
    def login(self):
        # Connection with HTTP or HTTPS
        if self.ssl:
            conn = httplib.HTTPSConnection(self.server, self.port)
        else:
            conn = httplib.HTTPConnection(self.server, self.port)
            
        conn.request('POST', '/auth', self.__encode({
            'username': self.username,
            'password': self.password
        }))
        response = conn.getresponse()
        conn.close()
        
        self.result = json.decoder(response.read())
        
        if response.status == 200:
            self.token = self.result['token']
            return True
        else:
            return False
    
    def logout(self):
        # Connection with HTTP or HTTPS
        if self.ssl:
            conn = httplib.HTTPSConnection(self.server, self.port)
        else:
            conn = httplib.HTTPConnection(self.server, self.port)
            
        conn.request('DELETE', '/auth', None, self.__encode({
            'Access-Token': self.token
        }))
        response = conn.getresponse()
        conn.close()
        
        self.result = json.decoder(response.read())
        
        return response.status == 200
    
    '''
    User API
    '''
    def getUser(self):
        if self.ssl:
            conn = httplib.HTTPSConnection(self.server, self.port)
        else:
            conn = httplib.HTTPConnection(self.server, self.port)
            
        conn.request('GET', '/user'+self.username, None, self.__encode({
            'Access-Token': self.token
        }))
        response = conn.getresponse()
        conn.close()
        
        self.result = json.decoder(response.read())
        
        return response.status == 200
    
    '''
    File API
    '''
    def getList(self):
        # Connection with HTTP or HTTPS
        if self.ssl:
            conn = httplib.HTTPSConnection(self.server, self.port)
        else:
            conn = httplib.HTTPConnection(self.server, self.port)
            
        conn.request('GET', '/file', None, self.__encode({
            'Access-Token': self.token
        }))
        response = conn.getresponse()
        conn.close()
        
        self.result = json.decoder(response.read())
        
        return response.status == 200
            