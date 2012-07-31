#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import httplib
import hashlib
import pyinotify
import json
import ConfigParser

class RNFileSystemSDK():
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
            self.config.write(open(self.config_path, 'wb'))
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
            self.config.write(open(self.config_path, 'wb'))
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

'''
File system event handler
'''
class EventHandler(pyinotify.ProcessEvent):
    # Delete
    def process_IN_DELETE(self, event):
        print "(X) DELETE %s" % event.pathname
    # Create
    def process_IN_CREATE(self, event):
        if os.path.isdir(event.pathname):
            print "(D) CREATE %s" % event.pathname
        else:
            print "(F) CREATE %s" % event.pathname
    # Modify
    def process_IN_MODIFY(self, event):
        if os.path.isdir(event.pathname):
            print "(D) MODIFY %s" % event.pathname
        else:
            print "(F) MODIFY %s" % event.pathname
    # Colse Write
    def process_IN_CLOSE_WRITE(self, event):
        if os.path.isdir(event.pathname):
            print "(D) CWRITE %s" % event.pathname
        else:
            print "(F) CWRITE %s" % event.pathname
    def process_IN_MOVED_FROM(self, event):
        if os.path.isdir(event.pathname):
            print "(D) MOVE F %s" % event.pathname
        else:
            print "(F) MOVE F %s" % event.pathname
    def process_IN_MOVED_TO(self, event):
        if os.path.isdir(event.pathname):
            print "(D) MOVE T %s" % event.pathname
        else:
            print "(F) MOVE T %s" % event.pathname

class LocalDisk():
    def __init__(self, config_path):
        self.config_path = config_path
        
        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.config_path)
        
        #self.local_path = '/tmp/RNFileSystem.Data'
        self.local_path = self.config.get('local', 'target')
    
    def __md5Checksum(self, filePath):
        fh = open(filePath, 'rb')
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()
    
    def getLocalList(self, path = ''):
        list = []
        current_path = self.local_path + path
        for dir in os.listdir(current_path):
            if os.path.isdir(current_path + '/' + dir):
                list.append({
                    path + '/' + dir: 0
                })
                list += self.getLocalList(path + '/' + dir)
            else:
                list.append({
                    path + '/' + dir: self.__md5Checksum(current_path + '/' + dir)
                })
        return list

'''
Reborn Server Client
'''
class RNFileSystemClient():
    def __init__(self):
        self.config_path = 'RNFileSystemClient.ini'
        
        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.config_path)
        
        # RNFS SDK
        self.RNFS = RNFileSystemSDK(self.config_path)
        
        # Local Disk
        self.local = LocalDisk(self.config_path)
        
        # Inotify event mask
        self.event_mask = 0
        self.event_mask |= pyinotify.IN_DELETE
        self.event_mask |= pyinotify.IN_CREATE
        self.event_mask |= pyinotify.IN_MODIFY
        self.event_mask |= pyinotify.IN_MOVED_TO
        self.event_mask |= pyinotify.IN_MOVED_FROM
        
        # Check root directory
        if os.path.exists(self.config.get('local', 'target')) == False:
            os.mkdir(self.config.get('local', 'target'))
        
        # Event Listener
        wm = pyinotify.WatchManager()
        wm.add_watch(self.config.get('local', 'target'), self.event_mask, rec=True, auto_add=True)
        self.notifier = pyinotify.Notifier(wm, EventHandler())
    
    '''
    Run Client
    '''
    def run(self):
        if self.RNFS.login():
            print "Token -"
            print self.RNFS.token;
            
            print "\nUser Information -"
            if(self.RNFS.getUser()):
                info = self.RNFS.getResult()
                for key in info:
                    print "%12s: %s" % (key, info[key])
                    
            print "\nServer List -"
            if(self.RNFS.getList()):
                server_list = []
                list = self.RNFS.getResult()
                list.pop('/')
                for path in list:
                    server_list.append(path)
                server_list = set(server_list)
                print server_list
            
            print "\nLocal List -"
            local_list = []
            for path in self.local.getLocalList():
                for key in path:
                    local_list.append(key)
            local_list = set(local_list)
            print local_list
            
            print "\nUL List"
            print local_list.difference(server_list)
            
            print "\nDL List"
            print server_list.difference(local_list)
            
            print "\nFixed List"
            print server_list.intersection(local_list)
                        
        else:
            print 'Login Failed'
            sys.exit()
        
#        self.notifier.loop()

if __name__ == '__main__':
    R = RNFileSystemClient()
    R.run()
    