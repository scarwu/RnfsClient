# -*- coding: utf-8 -*-
import os
import time
import hashlib
from threading import Thread

class Sync(Thread):
    def __init__(self, config, api, transfer, db):
        Thread.__init__(self)
        
        self.sync_time = config['sync_time']
        self.root = config['root']
        self.target = config['target']
        
        self.api = api
        self.transfer = transfer
        self.db = db
    
    def md5Checksum(self, file_path):
        fh = open(file_path, 'rb')
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()
    
    def getLocalList(self, path = ''):
        local_list = {}
        current_path = self.target + path
        for dirname in os.listdir(current_path):
            if os.path.isdir(current_path + '/' + dirname):
                local_list[path + '/' + dirname] = {
                    'type': 'dir'
                }
                local_list.update(self.getLocalList(path + '/' + dirname))
            else:
                local_list[path + '/' + dirname] = {
                    'type': 'file',
                    'hash': self.md5Checksum(current_path + '/' + dirname),
                    'size': os.path.getsize(current_path + '/' + dirname)
                }
        return local_list
    
#    def fileInfo(self, path):
#        if not os.path.exists(path):
#            return None
#        else:
#            return {
#                'hash': self.md5Checksum(self.target + '/' + path),
#                'size': os.path.getsize(self.target + '/' + path)
#            }
    
    def run(self):
        print "CS ... Start"
        while(1):
            time.sleep(self.sync_time)
            self.differ()
    
    def differ(self, wait=False):
        if(self.api.getUser()):
            user_info = self.api.getResult()
            print "User  %s - %d byte / %d byte / %d byte" % (
                user_info['username'],
                user_info['used'],
                user_info['capacity'],
                user_info['upload_limit']
            )
            print "Token %s" % self.api.token
        
        # Get cache list
        cache_list = self.db.get()
        cache_index = set(cache_list.keys())

        # Get local list
        local_list = self.getLocalList()
        local_index = set(local_list.keys())
        
        # Get server list
        if(self.api.getList()):
            server_list = {}
            for index in self.api.getResult().keys():
                server_list[index.encode('utf-8')] = self.api.getResult()[index]
            server_list.pop('/')
            server_index = set(server_list.keys())
        else:
            print self.api.getResult()
            print 'CS ... Exit'
            os.sys.exit()
        
        # Delete Index
        local_delete_index = list(cache_index.intersection(local_index).difference(server_index))
        server_delete_index = list(cache_index.intersection(server_index).difference(local_index))
        
        # Upload / Download Index
        upload_index = list(local_index.difference(cache_index.union(server_index)))
        download_index = list(server_index.difference(cache_index.union(local_index)))
        
        # Identical Index
        identical_index = list(server_index.intersection(local_index))
        
        local_delete_index.sort(reverse=True)
        server_delete_index.sort(reverse=True)
        upload_index.sort()
        download_index.sort()
        
        file_list = {}
        for index in identical_index:
            file_list[index] = server_list[index]
        
        # Generate List
        upload_list = []
        for path in upload_index:
            if local_list[path]['type'] == 'dir':
                upload_list.append({
                    'path': path,
                    'type': 'dir'
                })
            else:
                upload_list.append({
                    'path': path,
                    'type': 'file',
                    'size': local_list[path]['size'],
                    'hash': local_list[path]['hash'],
                    'version': 0
                })
        
        download_list = []
        for path in download_index:
            if server_list[path]['type'] == 'dir':
                download_list.append({
                    'path': path,
                    'type': 'dir'
                })
            else:
                download_list.append({
                    'path': path,
                    'type': 'file',
                    'size': server_list[path]['size'],
                    'hash': server_list[path]['hash'],
                    'version': server_list[path]['version']
                })
        
        # Delete Local Files
        for index in local_delete_index:
            print '--- LD: %s' % index
            if os.path.isdir(self.target + '/' + index):
                os.rmdir(self.target + '/' + index)
            else:
                os.remove(self.target + '/' + index)
            self.db.delete(index)
        
        # Delete Server Files
        for index in server_delete_index:
            print '--- SD: %s' % index
            self.api.deleteFile(index)
            self.db.delete(index)
        
        self.transfer.upload(upload_list);
        self.transfer.download(download_list);
#        self.transfer.update(update_list);

        if wait:
            self.transfer.wait()
        