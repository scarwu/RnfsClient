# -*- coding: utf-8 -*-

import os
import json
import random
import urllib2
import httplib
import hashlib

class API():
    def __init__(self, config):
        self.config = config
        self.status = 0
        self.result = None
        self.error_count = 0
    
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

    def __getConnectInstance(self, alive_time = None):
        if self.config['ssl']:
            return httplib.HTTPSConnection(self.config['host'], self.config['port'], timeout=alive_time)
        else:
            return httplib.HTTPConnection(self.config['host'], self.config['port'], timeout=alive_time)

    def getResult(self):
        return self.result
    
    def getStatus(self):
        return self.status
    
    '''
    Authentication API
    '''
    def __updateToken(self):
        conn = self.__getConnectInstance()
        conn.request('PUT', '/auth', None, {'Access-Token': self.config['token']})
        
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        
        conn.close()
        return response.status == 200
    
    def login(self):
        if self.__updateToken():
            return True
            
        conn = self.__getConnectInstance()
        conn.request('POST', '/auth', self.__encode({
            'username': self.config['username'],
            'password': self.config['password']
        }))
        
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        self.status = response.status
        conn.close()
        
        if response.status == 200:
            self.config['token'] = self.result['token']

        return response.status == 200
    
    def logout(self):
        conn = self.__getConnectInstance()
        conn.request('DELETE', '/auth', None, {'Access-Token': self.config['token']})
        
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
        conn.request('GET', '/user/'+self.config['username'], None, {'Access-Token': self.config['token']})
        
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
        conn.request('GET', '/file', None, {'Access-Token': self.config['token']})
        
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        self.status = response.status
        
        conn.close()
        
        return response.status == 200
    
    def downloadFile(self, server_path, local_path):
        conn = self.__getConnectInstance()
        conn.request('GET', urllib2.quote('/file/' + server_path.lstrip('/')), None, {'Access-Token': self.config['token']})
        
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
        if local_path == None:
            conn.request('POST', urllib2.quote('/file/' + server_path.lstrip('/')), None, {'Access-Token': self.config['token']})
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

            conn.request('POST', urllib2.quote('/file/' + server_path.lstrip('/')), '\r\n'.join(body), {
                'Accept': 'text/plain',
                'Access-Token': self.config['token'],
                'Content-Type': 'multipart/form-data; boundary=%s' % bundary
            })
        
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        self.status = response.status
        
        conn.close()
        
        return response.status == 200
    
    def deleteFile(self, server_path):
        conn = self.__getConnectInstance()
        conn.request('DELETE', urllib2.quote('/file/' + server_path.lstrip('/')), None, {'Access-Token': self.config['token']})
        
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        self.status = response.status
        
        conn.close()
        
        return response.status == 200
    
    '''
    Sync API
    '''
    def sendPolling(self, alive_time):
        conn = self.__getConnectInstance(alive_time)
        conn.request('POST', '/sync/'+self.config['username'], None, {'Access-Token': self.config['token']})
        
        response = conn.getresponse()
        self.result = self.__decode(response.read())
        self.status = response.status
        
        conn.close()
        
        return response.status == 200
