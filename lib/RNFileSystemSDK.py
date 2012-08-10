# -*- coding: utf-8 -*-

import os
import json
import random
import urllib2
import httplib
import hashlib
import ConfigParser

class API():
    def __init__(self, config):
        self.username = config['username']
        self.password = config['password']
        self.token = config['token']
        
        self.host = config['host']
        self.port = config['port']
        self.ssl = config['ssl']
        
        self.status = 0
        self.result = None
    
    '''
    JSON Encoder
    '''
    def __encode(self, data):
        return json.dumps(data, separators=(',', ':'))
    
    def __decode(self, data):
        if data == '':
            return None
        else:
            try:
                return json.loads(data)
            except:
                return data

    def __getConnectInstance(self):
        if self.ssl:
            return httplib.HTTPSConnection(self.host, self.port)
        else:
            return httplib.HTTPConnection(self.host, self.port)

    def getResult(self):
        return self.result
    
    def getStatus(self):
        return self.status
    
    '''
    Authentication API
    '''
    def __updateToken(self):
        conn = self.__getConnectInstance()
        conn.request('PUT', '/auth', None, {'Access-Token': self.token})
        
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        
        conn.close()
        return response.status == 200
    
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
        self.status = response.status
        conn.close()
        
        if response.status == 200:
            self.token = self.result['token']

        return response.status == 200
    
    def logout(self):
        conn = self.__getConnectInstance()
        conn.request('DELETE', '/auth', None, {'Access-Token': self.token})
        
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        self.status = response.status
        
        conn.close()
        
        return response.status == 200
    
    '''
    User API
    '''
    def getUser(self):
        conn = self.__getConnectInstance()
        conn.request('GET', '/user/'+self.username, None, {'Access-Token': self.token})
        
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        self.status = response.status
        
        conn.close()
        
        return response.status == 200
    
    '''
    File API
    '''
    def getList(self):
        conn = self.__getConnectInstance()
        conn.request('GET', '/file', None, {'Access-Token': self.token})
        
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        self.status = response.status
        
        conn.close()
        
        return response.status == 200
    
    def downloadFile(self, server_path, local_path):
        conn = self.__getConnectInstance()
        conn.request('GET', urllib2.quote('/file' + server_path), None, {
            'Access-Token': self.token
        })
        
        response = conn.getresponse()

        if response.status == 200:
            os.path.dirname(local_path)
            file(local_path,"wb").write(response.read())
            self.result = None
        else:
            self.result = self.__decode(response.read())
            
        self.status = response.status

        conn.close()
        
        return response.status == 200
    
    def uploadFile(self, server_path, local_path = None):
        conn = self.__getConnectInstance()
        
        url = urllib2.quote('/file' + server_path)
        
        if local_path == None:
            conn.request('POST', url, None, {'Access-Token': self.token})
        else:
            m = hashlib.md5()
            m.update('%f' % random.random())
            bundary = m.hexdigest()
            body = []

            file_content = file(local_path, 'rb').read()

            body.extend([
                '--' + bundary,
                'Content-Disposition: form-data; name="file"; filename="%s"' % os.path.basename(local_path),
                'Content-Type: application/octet-stream',
                '',
                file_content,
                '--' + bundary + '--',
                ''
            ])

            conn.request('POST', url, '\r\n'.join(body), {
                'Accept': 'text/plain',
                'Access-Token': self.token,
                'Content-Type': 'multipart/form-data; boundary=%s' % bundary
            })
        
        response = conn.getresponse()

        if response.status == 200:
            self.result = None
        else:
            self.result = self.__decode(response.read())

        self.status = response.status
        
        conn.close()
        
        return response.status == 200
    
    '''
    Sync API
    '''
    def sendPolling(self, alive_time):
        conn = self.__getConnectInstance()
        conn.request('POST', '/sync/'+self.username, None, {'Access-Token': self.token})
        
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        self.status = response.status
        
        conn.close()
        
        return response.status == 200