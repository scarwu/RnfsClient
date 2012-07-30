#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib
import json
import ConfigParser

class RNFileSystemSDK():
    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read('RNFileSystemClient.cfg')
        
        self.username = self.config.get('info', 'username')
        self.password = self.config.get('info', 'password')
        self.token = self.config.get('info', 'token')
        self.server = self.config.get('server', 'host')
        self.port = self.config.getint('server', 'port')
        self.ssl = self.config.getboolean('server', 'ssl')

    def __encode(self, data):
        return json.dumps(data, separators=(',', ':'))
    
    def __decode(self, data):
        if data == '':
            return None
        else:
            return json.loads(data)

    def getResult(self):
        return self.result
    
    '''
    Authentication API
    '''
    def __updateToken(self):
        if self.ssl:
            conn = httplib.HTTPSConnection(self.server, self.port)
        else:
            conn = httplib.HTTPConnection(self.server, self.port)
            
        conn.request('PUT', '/auth', None, {
            'Access-Token': self.token
        })
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        
        conn.close()

        if response.status == 200:
            return True
        else:
            return False
    
    def login(self):
        if self.__updateToken():
            return True
            
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
        self.result = self.__decode(response.read())
        
        conn.close()
        
        if response.status == 200:
            self.token = self.result['token']
            
            # Write-back
            self.config.set('info', 'token', self.token)
            self.config.write(open('RNFileSystemClient.cfg', 'wb'))
            return True
        else:
            return False
    
    def logout(self):
        # Connection with HTTP or HTTPS
        if self.ssl:
            conn = httplib.HTTPSConnection(self.server, self.port)
        else:
            conn = httplib.HTTPConnection(self.server, self.port)
            
        conn.request('DELETE', '/auth', None, {
            'Access-Token': self.token
        })
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        
        conn.close()
        
        if response.status == 200:
            # Write-back
            self.config.set('info', 'token', '')
            self.config.write(open('RNFileSystemClient.cfg', 'wb'))
            return True
        else:
            return False
    
    '''
    User API
    '''
    def getUser(self):
        if self.ssl:
            conn = httplib.HTTPSConnection(self.server, self.port)
        else:
            conn = httplib.HTTPConnection(self.server, self.port)
            
        conn.request('GET', '/user/'+self.username, None, {
            'Access-Token': self.token
        })
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        
        conn.close()
        
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

        conn.request('GET', '/file', None, {
            'Access-Token': self.token
        })
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        
        conn.close()
        
        return response.status == 200