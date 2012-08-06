import os
import hashlib
import ConfigParser

class FileHandler():
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