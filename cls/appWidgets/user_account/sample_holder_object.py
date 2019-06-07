'''
Created on Dec 2, 2016

@author: bergr    
'''
import os

class sample_pos_obj(object):
    def __init__(self, pos=1):
        super(sample_pos_obj, self).__init__()
        self.pos = pos
        self.name = 'pos%d' % pos
        self.notes = ""
        self.approx_xcenter = 0.0
        self.approx_ycenter = 0.0
        
class sample_holder_obj(object):
    def __init__(self, userName, id='H110212', base_data_dir='c:\data'):
        super(sample_holder_obj, self).__init__()
        self.id = id
        self._userName = userName
        self._pos = []
        
        for pos in range(1,7):
            self._pos.append(sample_pos_obj(pos))
            
        self._data_dir = os.path.join(base_data_dir, str(self.id))
        self.make_basedata_dir()
        #self.make_data_dirs()
    
    def get_base_data_dir(self):
        return self._data_dir
    
    def get_pos_dir(self, pos):
        """
        convienience function to retrieve the directory to where a positions data is located
        """
        return os.path.join(self._data_dir, self._pos[pos].name)
    
    def make_basedata_dir(self):
        if os.path.exists(self._data_dir):
            pass
        else:
            os.mkdir(self._data_dir)
    
    def make_data_dirs(self):
        for p in self._pos:
            posPath = os.path.join(self._data_dir, p.name)
            if os.path.exists(posPath):
                pass
                #print 'data dir [%s] already exists' % self._data_dir
                #that sequence number already exists so try next one
            else:
                #use this one
                os.mkdir(posPath)
    




if __name__ == '__main__':
    pass