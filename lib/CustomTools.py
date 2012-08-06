import os
import hashlib
import ConfigParser

class FileHandler():
    def __init__(self, config_path):
        self.config_path = config_path

        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.config_path)
        
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
        local_list = {}
        current_path = self.local_path + path
        for dirname in os.listdir(current_path):
            if os.path.isdir(current_path + '/' + dirname):
                local_list[path + '/' + dirname] = {
                    'type': 'dir'
                }
                local_list.update(self.getLocalList(path + '/' + dirname))
            else:
                local_list[path + '/' + dirname] = {
                    'type': 'file',
                    'hash': self.__md5Checksum(current_path + '/' + dirname)
                }
        return local_list