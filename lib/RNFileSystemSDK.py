#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib
import json
import ConfigParser
import os

class API():
    def __init__(self, config_path):
        self.config_path = config_path
        
        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.config_path)
        
        self.username = self.config.get('info', 'username')
        self.password = self.config.get('info', 'password')
        self.token = self.config.get('info', 'token')
        self.server = self.config.get('server', 'host')
        self.port = self.config.getint('server', 'port')
        self.ssl = self.config.getboolean('server', 'ssl')
    
    def __send(self, config):
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
    JSON Encoder
    '''
    def __encode(self, data):
        return json.dumps(data, separators=(',', ':'))
    
    def __decode(self, data):
        if data == '':
            return None
        else:
            return json.loads(data)

    def __getConnectInstance(self):
        if self.ssl:
            return httplib.HTTPSConnection(self.server, self.port)
        else:
            return httplib.HTTPConnection(self.server, self.port)

    def getResult(self):
        return self.result
    
    '''
    Authentication API
    '''
    def __updateToken(self):
        conn = self.__getConnectInstance()
            
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
            
        conn = self.__getConnectInstance()
            
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
            self.config.write(open(self.config_path, 'wb'))
            return True
        else:
            return False
    
    def logout(self):
        conn = self.__getConnectInstance()
            
        conn.request('DELETE', '/auth', None, {
            'Access-Token': self.token
        })
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        
        conn.close()
        
        if response.status == 200:
            # Write-back
            self.config.set('info', 'token', '')
            self.config.write(open(self.config_path, 'wb'))
            return True
        else:
            return False
    
    '''
    User API
    '''
    def getUser(self):
        conn = self.__getConnectInstance()
            
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
        conn = self.__getConnectInstance()

        conn.request('GET', '/file', None, {
            'Access-Token': self.token
        })
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        
        conn.close()
        
        return response.status == 200
    
    def downloadFile(self, server_path, local_path):
        conn = self.__getConnectInstance()
        
        conn.request('GET', '/file' + server_path, None, {
            'Access-Token': self.token
        })
        response = conn.getresponse()
        
        os.path.dirname(local_path)
        
        f = open(local_path,"wb")
        f.write(response.read())
        f.close()
        
        self.result = None
        
        conn.close()
        
        return response.status == 200
    
    def uploadFile(self, server_path, local_path):
        conn = self.__getConnectInstance()

        f = open(local_path,"rb")
        conn.request('POST', '/file' + server_path, f.read(), {
            'Access-Token': self.token
        })
        f.close()
        
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        
        conn.close()
        
        return response.status == 200
    