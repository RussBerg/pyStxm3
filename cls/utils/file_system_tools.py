'''
Created on May 6, 2016

@author: control
'''
import os

def is_locked(filepath):
    """Checks if a file is locked by opening it in append mode.
    If no exception thrown, then the file is not locked.
    """
    locked = None
    file_object = None
    if os.path.exists(filepath):
        try:
            #print "Trying to open %s." % filepath
            buffer_size = 8
            # Opening file in append mode and read the first 8 characters.
            file_object = open(filepath, 'a', buffer_size)
            if file_object:
                #print "%s is not locked." % filepath
                locked = False
        except IOError as message:
            #print "File is locked (unable to open in append mode). %s." % message
            locked = True
        finally:
            if file_object:
                file_object.close()
                #print "%s closed." % filepath
    else:
        print("%s not found." % filepath)
    return locked

def is_stack_dir(data_dir):
    if(len(data_dir) > 0):
        d_lst = split_data_dir(data_dir)
        dname = d_lst[-1]
        fstr = os.path.join(data_dir, dname,'.hdf5')
        if(os.path.exists(fstr)):
            return(True)
        else:
            return(False)
    else:
        print('Invalid data directory')
        return(False)    

def split_data_dir(data_dir):    
    if(data_dir == None):
        return
    if(data_dir.find('/') > -1):
        data_dir = data_dir.replace('/','\\')
            
    if(data_dir.find('\\') > -1):
        sep = '\\'
    #elif(data_dir.find('/') > -1):
    #    sep = '/'
    else:
        print('Unsupported directory string [%s]' % data_dir)
                
    d_lst = data_dir.split(sep)
    return(d_lst)

def get_filenames_in_dir(path, extension='hdf5'):
    if(os.path.isdir(path)):
        files = []
        for file in os.listdir(path):
            if(file.find(extension) > -1):
            #if file.endswith(".%s"%extension):
                files.append(file)
        return(sorted(files))
    return([])

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def skip_non_standard_dirs(dirs, prefix_char='C'):
    dirs_with_prefix = []
    f = lambda x: (x[0] is prefix_char)
    valid_ = list(map(f, dirs))
    for i in range(len(dirs)):
        if (valid_[i]):
            dirs_with_prefix.append(dirs[i])
    n_dirs = []
    for dir in dirs_with_prefix:
        if(dir.find(' ') > -1):
            pass
        elif(hasNumbers(dir)):
            n_dirs.append(dir)
        else:
            pass
    return(n_dirs)

def get_next_dir_in_seq_num(path, prefix_char='C', extension='hdf5'):

    if(os.path.isdir(path)):
        _dirs = sorted(next(os.walk(path))[1])
        _dirs = skip_non_standard_dirs(_dirs, prefix_char=prefix_char)
        if(len(_dirs) > 0):
            seq_num_str = _dirs[-1].replace(prefix_char,'')
            seq_num = int(seq_num_str) + 1
            return(seq_num)
        else:
            return(generate_new_seq_num(path, prefix_char, extension))
        
    return(generate_new_seq_num(path, prefix_char))    

def get_next_file_num_in_seq(path, prefix_char='C',extension='hdf5'):
    _files = get_filenames_in_dir(path, extension)
    if(len(_files) is 0):
        _files = get_filenames_in_dir(path, extension + '.tmp')
    if (len(_files) is 0):
        _files = get_filenames_in_dir(path, extension + '.idx')
    if (len(_files) is 0):
        _files = get_filenames_in_dir(path, extension + '.err')

    if(len(_files) > 0):
        seq_num_str = _files[-1].replace(prefix_char,'').replace('.%s'%extension,'')
        seq_num_str = seq_num_str.replace('.tmp','')
        seq_num_str = seq_num_str.replace('.idx', '')
        seq_num_str = seq_num_str.replace('.err', '')
        #seq_num = int(seq_num_str) + 1
        seq_num = int(seq_num_str) + 1

        if(check_if_tmp_or_final_exist(path, seq_num, prefix_char=prefix_char, extension=extension)):
            #skip over the tmp/final file sequence number
            seq_num = seq_num + 1

        return(seq_num)
    else:
        return(generate_new_seq_num(path, prefix_char))

def get_next_dir_in_seq(path, prefix_char='C'):
    if(os.path.isdir(path)):
        _dirs = sorted(next(os.walk(path))[1])
        if(len(_dirs) > 0):
            seq_num_str = _dirs[-1].replace(prefix_char,'')
            seq_num = int(seq_num_str) + 1
            return(prefix_char + str(seq_num))
        else:
            return(generate_new_seq_name(path, prefix_char))
    return(generate_new_seq_name(path, prefix_char))
    
def get_next_file_in_seq(path, prefix_char='C',extension='hdf5'):
    return(get_next_file_num_in_seq(path, prefix_char=prefix_char, extension=extension))
    # _files = get_filenames_in_dir(path, extension)
    # if(len(_files) > 0):
    #     seq_num_str = _files[-1].replace(prefix_char,'').replace('.%s'%extension,'')
    #     seq_num = int(seq_num_str) + 1
    #     return(prefix_char + str(seq_num))
    # else:
    #     return(generate_new_seq_name(path, prefix_char))
    
    
def generate_new_seq_num(path, prefix_char='C', extension='hdf5'):
    """
        generate_new_seq_num: This function takes a path to the base directory to be searched and returns with the
        directory name that represents the next in the sequence

        :param path: path description
        :type path: path type

        :returns: None
    """
    import os, datetime
    t = datetime.datetime.now()
    if(os.path.isdir(path)):
        _dirs = next(os.walk(path))[1]
        files = get_filenames_in_dir(path, extension)
        seq_num = len(files)  
        if(seq_num == 0):
            return(get_directory_number(path, prefix_char='C'))
        fname = '%s%s%03d' % (prefix_char, t.strftime("%y%m%d"), seq_num)
        full_seq_num  = '%s%03d' % (t.strftime("%y%m%d"), seq_num)
        while fname in _dirs:
            seq_num += 1 
            fname = '%s%s%03d' % (prefix_char, t.strftime("%y%m%d"), seq_num)
            full_seq_num = '%s%03d' % (t.strftime("%y%m%d"), seq_num)
    
        return(int(full_seq_num))    
    else:
        #print 'base directory doesnt exist'
        return(None)

def generate_new_seq_name(path, prefix_char='C', extension='hdf5'):
    """
        generate_new_seq_dirname: This function takes a path to the base directory to be searched and returns with the
        directory name that represents the next in the sequence

        :param path: path description
        :type path: path type

        :returns: None
    """
    if(os.path.isdir(path)):
        import datetime
        t = datetime.datetime.now()
        _dirs = next(os.walk(path))[1]
        files = get_filenames_in_dir(path, )
        seq_num = len(files)  
        fname = '%s%s%03d' % (prefix_char, t.strftime("%y%m%d"), seq_num)
           
        while fname in _dirs:
            seq_num += 1 
            fname = '%s%s%03d' % (prefix_char, t.strftime("%y%m%d"), seq_num)
    
        return(fname)
    else:
        return(None)
    
def get_next_seq_num(path, prefix_char='C', extension='hdf5'):
    '''
    main function to get next file or directory sequence number
    '''
    dir_num =  get_next_dir_in_seq_num(path, prefix_char, extension)
    file_num = get_next_file_num_in_seq(path, prefix_char)
    if(file_num > dir_num):
        return(file_num)
    else:
        return(dir_num)   

def check_if_tmp_or_final_exist(path, file_num, prefix_char='C', extension='hdf5'):
    tmp_fname = '%s/%c%d.%s.tmp' % (path, prefix_char, file_num, extension)
    final_fname = '%s/%c%d.%s.final' % (path, prefix_char, file_num, extension)
    if(os.path.exists(tmp_fname)):
        return(True)
    if (os.path.exists(final_fname)):
        return (True)
    return(False)

def get_directory_number(path, prefix_char='C'):
    import os, datetime
    t = datetime.datetime.now()
    d_lst = split_data_dir(path)
    dnum = int(d_lst[-1].replace(prefix_char, ''))
    if(dnum < 5000):
        dnum = int('%s%03d' % (t.strftime("%y%m%d"), 0))
    return(dnum)

def get_next_stack_thumbnail_seq_name(path, prefix_char='C', extension='jpg'):
    if(os.path.isdir(path)):
        dir_num = get_directory_number(path, prefix_char)
        num_jpgs = len(get_filenames_in_dir(path, extension))
        thumb_name = prefix_char + str(dir_num) + '_%03d' % num_jpgs
        return(thumb_name)
    else:
        return(None)

def get_stack_seq_num_from_fname(fname):
    if(fname.find('_') > -1):
        names = fname.split('_')
        num = int(names[1])
        return(names[0], num)
    else:
        return(fname, int(0))


def make_base_datafile_name_dct():
    dct = {}
    dct['thumb_name'] = None
    dct['prefix'] = None
    dct['data_ext'] = '.hdf5'
    dct['stack_dir'] = False
    dct['data_name'] = None
    dct['thumb_ext'] = 'jpg'
    return(dct)


#####################################################
def master_get_seq_names(path, prefix_char='C', thumb_ext='jpg', dat_ext='hdf5', stack_dir=False, num_desired_datafiles=1, new_stack_dir=False):
    '''
    master_get_seq_names: call this function to get a dict of what the next set of file and directory names should be, if the path given is a stack directory destination
    then the stack_dir flag must be set to True, else False.
    With a single call to this function a single or set of desired thumbnail and data file names can be generated.
    
    :param path: This is the path to the directory that the data will end up in
    :type path: string
    
    :param prefix_char: An example for the Cryo STXM is 'C' indicating that teh data was recorded on the Cryo STXM, 'A' for Ambient STXM
    :type prefix_char: string
    
    :param thumb_ext: the file extension of the thumbnail image: 'jpg'
    :type thumb_ext: string
    
    :param dat_ext: the file extension of the thumbnail image: 'hdf5'
    :type dat_ext: string
    
    :param stack_dir: indicates wether or not the path is a stack dorectry or not
    :type stack_dir: bool
    
    :param num_desired_datafiles: the number of thumbail image file entries to generate
    :type num_desired_datafiles: integer
    
    :returns: a dictionary of 
    
        ex: a single
        d = master_get_seq_names(path + '/' + new_stack_dirname, prefix_char='C', thumb_ext='jpg', dat_ext='hdf5', stack_dir=False)
        d = {
            0: {'thumb_name': 'C160506012', 'prefix': 'C160506012', 'data_ext': 'hdf5', 'stack_dir': 'C:\\controls\\py2.7\\Beamlines\\sm\\data\\guest\\May6/C160506012', 'data_name': 'C160506012.hdf5', 'thumb_ext': 'jpg'}
            }

        ex: a stack sequence of 5 files
        
        d = master_get_seq_names(path, prefix_char='C', thumb_ext='jpg', dat_ext='hdf5', stack_dir=True, num_desired_datafiles=5)
        d = {
            0: {'thumb_name': 'C160506010_000', 'prefix': 'C160506010', 'data_ext': 'hdf5', 'stack_dir': 'C:\\controls\\py2.7\\Beamlines\\sm\\data\\guest\\May6\\C160506010/C160506010', 'data_name': 'C160506010.hdf5', 'thumb_ext': 'jpg'}, 
            1: {'thumb_name': 'C160506010_001', 'prefix': 'C160506010', 'data_ext': 'hdf5', 'stack_dir': 'C:\\controls\\py2.7\\Beamlines\\sm\\data\\guest\\May6\\C160506010/C160506010', 'data_name': 'C160506010.hdf5', 'thumb_ext': 'jpg'}, 
            2: {'thumb_name': 'C160506010_002', 'prefix': 'C160506010', 'data_ext': 'hdf5', 'stack_dir': 'C:\\controls\\py2.7\\Beamlines\\sm\\data\\guest\\May6\\C160506010/C160506010', 'data_name': 'C160506010.hdf5', 'thumb_ext': 'jpg'}, 
            3: {'thumb_name': 'C160506010_003', 'prefix': 'C160506010', 'data_ext': 'hdf5', 'stack_dir': 'C:\\controls\\py2.7\\Beamlines\\sm\\data\\guest\\May6\\C160506010/C160506010', 'data_name': 'C160506010.hdf5', 'thumb_ext': 'jpg'}, 
            4: {'thumb_name': 'C160506010_004', 'prefix': 'C160506010', 'data_ext': 'hdf5', 'stack_dir': 'C:\\controls\\py2.7\\Beamlines\\sm\\data\\guest\\May6\\C160506010/C160506010', 'data_name': 'C160506010.hdf5', 'thumb_ext': 'jpg'}
            }
        
    '''
    
    if(os.path.isdir(path)):
        next_seq_num =  get_next_seq_num(path, prefix_char=prefix_char, extension=dat_ext )
        #if(is_stack_dir(path)):
        if(stack_dir):
            #print 'it is a stack directory'
            data_file_seq_num = get_directory_number(path, prefix_char=prefix_char)
            next_seq_num = data_file_seq_num
            #data_file_seq_num = next_seq_num
            #thumb_name = get_next_stack_thumbnail_seq_name(path + '/C' + str(data_file_seq_num), prefix_char='C', extension='jpg')
            thumb_name = get_next_stack_thumbnail_seq_name(path, prefix_char=prefix_char, extension=thumb_ext)
            
        else:
            #print 'it is not a stack directory'
            data_file_seq_num = next_seq_num
            thumb_name = prefix_char + str(next_seq_num)
        
        dct = make_base_datafile_name_dct()
        
        dct['data_dir'] = (path)
                
        if(next_seq_num is not None):
            dct['stack_dir'] = (os.path.join(path, prefix_char + str(next_seq_num)))
            dct['prefix'] = prefix_char + str(next_seq_num)
            dct['stack_flbl'] = '%s.%s img/%d' % (prefix_char + str(next_seq_num), dat_ext, 0)
            if(thumb_name is None):
                dct['thumb_name'] = '%s_000' % (dct['prefix'])
            else:
                dct['thumb_name'] = '%s' % (thumb_name)    
            
            dct['data_name'] = '%s.%s' % (prefix_char + str(data_file_seq_num), dat_ext)
        else:
            print('base directory [%s] does not exist' % path)
        
        dct['data_ext'] = dat_ext
        dct['thumb_ext'] = thumb_ext
        n_dct = {}
#         if(num_desired_datafiles == 1):
#             # make a new filename entry for each num_desired_datafiles
#             n_dct[0] = dct.copy()
#             next_seq_num += 1
#             n_dct[0]['prefix'] = prefix_char + str(next_seq_num)
#             n_dct[0]['thumb_name'] = prefix_char + str(next_seq_num)
#             n_dct[0]['data_name'] = '%s.%s' % (prefix_char + str(next_seq_num), dat_ext)
#             n_dct[0]['stack_flbl'] = '%s.%s img/%d' % (prefix_char + str(next_seq_num), dat_ext, 0)
#             
#         el
        if(num_desired_datafiles > 1):
            i = 0
            if(stack_dir):
                #images indexed by number in dict
                print('generate a sequence from the existing name')
                name, num = get_stack_seq_num_from_fname(dct['thumb_name'])
                
                for j in range(num, num + int(num_desired_datafiles)):
                    n_dct[i] = dct.copy()
                    n_dct[i]['thumb_name'] = name + '_%03d' % j
                    #n_dct[i]['stack_flbl'] = '%s.%s' % (prefix_char + str(j), dat_ext)
                    i += 1
            elif(new_stack_dir):
                print('generate a sequence from the existing name')
                name, num = get_stack_seq_num_from_fname(dct['thumb_name'])
                
                for j in range(num, num + int(num_desired_datafiles)):
                    n_dct[i] = dct.copy()
                    n_dct[i]['thumb_name'] = '%s_%03d' % ((prefix_char + str(data_file_seq_num)), j)
                    n_dct[i]['stack_flbl'] = '%s.%s img/%d' % ((prefix_char + str(data_file_seq_num)), dat_ext, j)
                    i += 1        
            else:
                # make a new filename entry for each num_desired_datafiles
                i = 1
                n_dct[0] = dct.copy()
                next_seq_num += 1
                for j in range(next_seq_num, next_seq_num + int(num_desired_datafiles-1)):
                    n_dct[i] = dct.copy()
                    n_dct[i]['prefix'] = prefix_char + str(j)
                    n_dct[i]['thumb_name'] = prefix_char + str(j)
                    n_dct[i]['data_name'] = '%s.%s' % (prefix_char + str(j), dat_ext)
                    n_dct[i]['stack_flbl'] = '%s.%s img/%d' % (prefix_char + str(j), dat_ext, i)
                    i += 1        
            
        else:
            #single image only
            n_dct = {}
            n_dct[0] = dct.copy()    
        
        return(n_dct)        
    else:
        return(None)

def get_data_file_name_list(dct):
    l = []
    for k in list(dct.keys()):
        l.append(dct[k]['data_name'])
    return(l)

def get_thumb_file_name_list(dct):
    l = []
    for k in list(dct.keys()):
        l.append(dct[k]['stack_flbl'])
    return(l)      
    
    

if __name__ == '__main__':
    #path = r'C:\controls\py2.7\Beamlines\sm\data\guest\Apr29'
    
    
#     path = r'C:\controls\py2.7\Beamlines\sm\data\guest\Apr29'
#     print 'what about [%s]' % path
#     d = master_get_seq_names(path, prefix_char='C', thumb_ext='jpg', dat_ext='hdf5', stack_dir=False)
#     print d
#     print
#     
#     
#     path = r'C:\controls\py2.7\Beamlines\sm\data\guest\May5'
#     print 'what about [%s]' % path
#     d = master_get_seq_names(path, prefix_char='C', thumb_ext='jpg', dat_ext='hdf5', stack_dir=False)
#     print d
#     print
#     
#     path = r'C:\controls\py2.7\Beamlines\sm\data\guest\May6'
#     print 'what about [%s]' % path
#     d = master_get_seq_names(path, prefix_char='C', thumb_ext='jpg', dat_ext='hdf5', stack_dir=False)
#     print d
#     print
#     
#     path = r'C:\controls\py2.7\Beamlines\sm\data\guest\May6'
#     print ' I want a new Stack dir in this directory [%s]' % path
#     new_stack_dirname = get_next_dir_in_seq(path)
#     print ' and that directory shall be called %s' % new_stack_dirname
#     print ' what about %s' % path + '/' + new_stack_dirname
#     d = master_get_seq_names(path + '/' + new_stack_dirname, prefix_char='C', thumb_ext='jpg', dat_ext='hdf5', stack_dir=False)
#     if(d is None):
#         print 'the directory %s does not exist yet' % (path + '/' + new_stack_dirname)
#     else:
#         print d
#    
#     print 
#         
#     path = r'C:\controls\py2.7\Beamlines\sm\data\guest\May6\C160506009'
#     print 'what about [%s]' % path
#     d = master_get_seq_names(path, prefix_char='C', thumb_ext='jpg', dat_ext='hdf5', stack_dir=True, num_desired_datafiles=20)
#     print d
#     print
# 
# 
#     path = r'C:\controls\py2.7\Beamlines\sm\data\guest\May6\C160506010'
#     print 'what about [%s]' % path
#     d = master_get_seq_names(path, prefix_char='C', thumb_ext='jpg', dat_ext='hdf5', stack_dir=True, num_desired_datafiles=5)
#     print d
#     print
    
    path = r'S:\STXM-data\Cryo-STXM\2019\guest\0530'
    #path = r'W:\sm-user\STXM-data\Cryo-STXM\2016\guest\0908\C160908020'
    #print ' I want a new Stack dir in this directory [%s]' % path
    #new_stack_dirname = get_next_dir_in_seq(path)
    #print ' and that directory shall be called %s' % new_stack_dirname
    #print ' what about %s' % path + '\\' + new_stack_dirname
    #os.mkdir(path + '\\' + new_stack_dirname)
    d = master_get_seq_names(path , prefix_char='C', thumb_ext='jpg', dat_ext='hdf5', stack_dir=False, num_desired_datafiles=5, new_stack_dir=False)
    if(d is None):
        print('the directory %s does not exist yet' % (path))
    else:
        for k in list(d.keys()):
            print(d[k])
    
    
    