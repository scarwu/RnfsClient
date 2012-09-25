import os
import time
import hashlib
from threading import Thread

import ServerEvent
import FileEvent

class Sync(Thread):
    def __init__(self, config, api, transfer, db):
        Thread.__init__(self)
        
        self.sync_time = config['sync_time']
        self.root = config['root']
        self.target = config['target']
        
        self.api = api
        self.transfer = transfer
        self.db = db
    
    def run(self):
        print "CompleteSync Start"
        while(1):
            self.differ()
            
            self.long_polling = ServerEvent.LongPolling(self.target, self.api, self.transfer, self.db)
            self.file_event = FileEvent.EventListener(self.target, self.api, self.transfer, self.db)
            
            self.long_polling.start()
            self.file_event.start()
            
            time.sleep(self.sync_time)
            
            print 'LongPolling Stop'
            print 'FileEvent Stop'
            self.long_polling._Thread__stop()
            self.file_event._Thread__stop()
    
    def md5Checksum(self, file_path):
        fh = open(file_path, 'rb')
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()
    
    # Get Local Files List
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
                    'size': os.path.getsize(current_path + '/' + dirname),
                    'time': int(os.path.getctime(current_path + '/' + dirname))
                }
        return local_list

    
    # Recursive Remove Directory
    def reRmdir(self, path):
        for root, dirs, files in os.walk(path, topdown=False):
            try:
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            except:
                pass
    
    # Calculate File Indexes Differ
    def differ(self):
        print 'CompleteSync Differ'
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
            print 'CompleteSync Exit'
            os.sys.exit()
        
        # Delete Index
        local_delete_index = list(cache_index.intersection(local_index).difference(server_index))
        server_delete_index = list(cache_index.intersection(server_index).difference(local_index))
        
        # Upload / Download Index
        upload_index = list(local_index.difference(cache_index.union(server_index)))
        download_index = list(server_index.difference(cache_index.union(local_index)))
        
        # Same / Lost / Untrack Index
        lost_index = list(cache_index.difference(local_index.union(server_index)))
        same_index = list(server_index.intersection(local_index))
        
        local_delete_index.sort(reverse=True)
        server_delete_index.sort(reverse=True)
        upload_index.sort()
        download_index.sort()
        
        # Update List
        update_list = []
        for path in same_index:
            if local_list[path]['type'] != 'dir':
                if local_list[path]['hash'] != server_list[path]['hash']:
                    if int(local_list[path]['time']) >= int(server_list[path]['time']):
                        update_list.append({
                            'path': path,
                            'type': 'file',
                            'to': 'server'
                        })
                    else:
                        update_list.append({
                            'path': path,
                            'type': 'file',
                            'to': 'client'
                        })
        
        # Generate List
        upload_list = []
        for path in upload_index:
            upload_list.append({
                'path': path,
                'type': local_list[path]['type']
            })
        
        download_list = []
        for path in download_index:
            download_list.append({
                'path': path,
                'type': server_list[path]['type']
            })

        # Delete Lost Files
        for path in lost_index:
            print 'Delete DB Indexes: %s' % path
            self.db.delete(path)
        
        # Delete Local Files
        for path in local_delete_index:
            print 'Delete Local Files: %s' % path
            if os.path.isdir(self.target + path):
                self.reRmdir(self.target + path)
            else:
                os.remove(self.target + path)
            self.db.delete(path)
        
        # Delete Server Files
        for path in server_delete_index:
            print 'Delete Server Files: %s' % path
            self.api.deleteFile(path)
            self.db.delete(path)
        
        # Start File Handle
        self.transfer.upload(upload_list);
        self.transfer.download(download_list);
        self.transfer.update(update_list);

        self.transfer.wait()
        