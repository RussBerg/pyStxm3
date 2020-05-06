'''
Created on 2011-03-10

@author: bergr

These fileutils are designed to read data files produced by the CLS data acquisition system
'''
import os
import platform
import numpy
import time
from datetime import date

def get_module_name(fname):
    nm = fname.split(os.path.sep)[-1].replace('.py', '')
    return(nm)

def does_exist_on_disk(name):
    name = name.replace(' ', '')
    if os.path.exists(name):
        return (True)
    else:
        return (False)


def add_timestamp(filename):
    fname, ext = os.path.splitext(filename)
    # timestamp = time.strftime('-%Y_%m_%d_%H_%M_%S')
    dirDate = time.strftime('%Y_%m_%d')
    timestamp = time.strftime('-%H_%M_%S')
    # rebuild the filename
    new_filename = fname + timestamp + ext
    return (dirDate, new_filename)


# create a filename containing a sortable date-time stamp
def generate_datfile_name(scan_name, timeStamp=False):
    filename = scan_name + '.dat'
    if (timeStamp):
        directory, filename = add_timestamp(filename)
        return (directory, filename)

    return (filename)


def get_file_path_as_parts(fname):
    """ fname is a python string of the full path to a data file,
    then return the data_dir, file prefix and file suffix
    """
    fnameidx1 = fname.rfind('\\') + 1
    if (fnameidx1 == 0):
        fnameidx1 = fname.rfind('/') + 1
    fnameidx2 = fname.rfind('.')
    data_dir = fname[0: fnameidx1].replace('\\','/')
    if(fnameidx2 == -1):
        fprefix = fname[fnameidx1: ]
        fsuffix = ''
    else:
        fprefix = fname[fnameidx1: fnameidx2]
        fsuffix = fname[fnameidx2:]
    return (data_dir, fprefix, fsuffix)

# def get_file_path_as_parts(fname):
#     """ fname is a python string of the full path to a data file,
#     then return the data_dir, file prefix and file suffix
#     """
#     fnameidx1 = fname.rfind('\\') + 1
#     if (fnameidx1 == 0):
#         fnameidx1 = fname.rfind('/') + 1
#     fnameidx2 = fname.rfind('.')
#     data_dir = fname[0: fnameidx1]
#     fprefix = fname[fnameidx1: fnameidx2]
#     fsuffix = fname[fnameidx2:]
#     return (data_dir, fprefix, fsuffix)

def get_file_path_as_parts_with_dirs(fname):
    """ fname is a python string of the full path to a data file,
    then return the data_dir, file prefix and file suffix
    """
    fnameidx1 = fname.rfind('\\') + 1
    if (fnameidx1 == 0):
        fnameidx1 = fname.rfind('/') + 1
    fnameidx2 = fname.rfind('.')
    if (fnameidx2 == -1):
        # its most likely a directory
        data_dir = fname[0: fnameidx1]
        fprefix = fname[fnameidx1:]
        fsuffix = '<dir>'
    else:
        data_dir = fname[0: fnameidx1]
        fprefix = fname[fnameidx1: fnameidx2]
        fsuffix = fname[fnameidx2:]
    return (data_dir, fprefix, fsuffix)


def loadDatToArray(fileName, datType='int', delim=None):
    if (datType.find('float') > -1):
        d = numpy.float32
    elif (datType.find('int') > -1):
        d = numpy.int
    elif (datType.find('int8') > -1):
        d = numpy.int8
    elif (datType.find('char') > -1):
        d = numpy.char
    else:
        d = numpy.int

    if (delim):
        array = numpy.loadtxt(fileName, dtype=d, comments='#', delimiter=delim)
    else:
        array = numpy.loadtxt(fileName)
    return (array)


def loadDatTo2DArray(fileName, colX, colY):
    xyData = None
    if os.path.exists(fileName):
        # comments='#', delimiter=None,
        # array = numpy.loadtxt(fileName, dtype=numpy.float32, comments='#', delimiter='\t')
        array = numpy.loadtxt(fileName)
        xyData = array.take([colX, colY], axis=1)
    else:
        raise ValueError("numpy2qimage unable to open XIM file: file does not exist:", fileName)
        return None
    return xyData


def loadDatToXY(fileName, colX, colY):
    rawData = loadDatTo2DArray(str(fileName), colX, colY)
    # get the x column
    xx = rawData.take([0], axis=1)
    x = xx.reshape(len(xx), )
    # get the y column
    yy = rawData.take([1], axis=1)
    y = yy.reshape(len(yy), )
    return x, y


def readCSV(fname, as_dict=False):
    import csv
    contents = []
    with open(fname, 'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            # print row
            contents.append(row)

    if (as_dict):
        return (dict(contents))

    return (contents)


def writeCSV(csvList, fname):
    import csv
    with open(fname, 'wb') as f:
        writer = csv.writer(f)
        writer.writerows(csvList)


def readColumnStrs(fileName):
    if os.path.exists(fileName):
        # comments='#', delimiter=None,
        # return a dict of the column items
        columnStrs = {}
        colNums = 0
        f = open(fileName, 'r')
        strs = f.readlines()

        for l in strs:

            if (l.find('# column ') > -1):
                # grab remaining string after the # column
                l2 = l.replace('# ', '')
                # separate into column num and column ID string
                l3 = l2.split(': ')
                colNum = l3[0]
                # strip old NO CONNECTION messages
                evItem = l3[1].replace('NO CONNECTION', '')
                evItem = evItem.lstrip()
                evItem = evItem.rstrip()
                columnStrs[colNums] = {colNum: evItem}
                colNums += 1

        return columnStrs

    else:
        raise ValueError("readColumnStrs: hemeraged on file [%s]:", fileName)
        return None


def getColNumAndItem(columnStrs, index):
    item = columnStrs[index]
    i = list(item.keys())
    colnumStr = i[0]
    itemStr = item[colnumStr]
    return colnumStr, itemStr


def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    t_s = None
    if platform.system() == 'Windows':
        t_s = os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            t_s = stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            t_s = stat.st_mtime
            return(date.fromtimestamp(t_s))

    date_time = date.fromtimestamp(t_s)
    return(date_time)

if __name__ == '__main__':
    # #example loading data into a 2d array pull columns 1 and 2 as x and y respectively from the datafile
    # twoDData = loadDatTo2DArray(r'C:\pythonxy\workspace\sylmandWirescanViewer\src\data\1scan.dat', 1, 2)
    #
    # #example
    # #pull columns 1 and 2 as x and y respectively from the datafile
    # x,y = loadDatToXY(r'C:\pythonxy\workspace\sylmandWirescanViewer\src\data\1scan.dat', 1, 2)
    #
    # #example reading out the 'column' strings
    # colStrs =  readColumnStrs(r'C:\pythonxy\workspace\sylmandWirescanViewer\src\data\1scan.dat')
    # for l in range(0,len(colStrs)):
    # 	colnumStr, itemStr = getColNumAndItem(colStrs, l)
    # 	print('cols[%d] = %s, %s' % (l, colnumStr, itemStr))

    # date_time = creation_date(r'C:\controls\git_sandbox\pyStxm3\cls\scanning\e712_wavegen\ddl_data\ddl_data.hdf5')
    # print("Date time object:", date_time)
    flst = ['C:/controls/stxm-data/guest/0110\..',
        'C:/controls/stxm-data/guest/0110\..',
        'C:/controls/stxm-data/guest/0110\C200110001.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110001.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110001.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110002.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110002.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110002.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110007.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110007.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110007.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110008.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110008.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110008.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110009.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110009.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110009.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110010.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110010.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110010.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110011.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110011.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110011.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110012.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110012.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110012.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110013.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110013.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110013.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110014.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110014.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110014.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110015.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110015.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110015.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110016.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110016.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110016.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110017.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110017.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110017.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110018.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110018.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110018.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110019.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110019.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110019.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110020.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110020.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110020.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110021.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110021.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110021.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110022.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110022.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110022.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110023.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110023.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110023.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110024.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110024.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110024.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110025.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110025.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110025.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110026.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110026.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110026.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110027.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110027.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110027.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110028.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110028.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110028.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110029.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110029.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110029.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110030.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110030.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110030.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110031.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110031.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110031.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110032.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110032.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110032.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110033.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110033.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110033.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110034.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110034.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110034.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110035.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110035.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110035.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110036.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110036.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110036.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110037.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110037.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110037.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110038.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110038.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110038.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110039.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110039.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110039.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110040.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110040.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110040.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110041',
        'C:/controls/stxm-data/guest/0110\C200110041\C200110041.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110041/C200110041.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110041/C200110041.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110042',
        'C:/controls/stxm-data/guest/0110\C200110042\C200110042.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110042/C200110042.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110042/C200110042.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110043',
        'C:/controls/stxm-data/guest/0110\C200110043\C200110043.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110043/C200110043.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110043/C200110043.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110044',
        'C:/controls/stxm-data/guest/0110\C200110044\C200110044.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110044/C200110044.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110044/C200110044.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110045',
        'C:/controls/stxm-data/guest/0110\C200110045\C200110045.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110045/C200110045.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110045/C200110045.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110046',
        'C:/controls/stxm-data/guest/0110\C200110046\C200110046.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110046/C200110046.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110046/C200110046.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110047',
        'C:/controls/stxm-data/guest/0110\C200110047\C200110047.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110047/C200110047.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110047/C200110047.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110048',
        'C:/controls/stxm-data/guest/0110\C200110048\C200110048.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110048/C200110048.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110048/C200110048.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110049',
        'C:/controls/stxm-data/guest/0110\C200110049\C200110049.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110049/C200110049.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110049/C200110049.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110050',
        'C:/controls/stxm-data/guest/0110\C200110050\C200110050.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110050/C200110050.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110050/C200110050.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110051',
        'C:/controls/stxm-data/guest/0110\C200110051\C200110051.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110051/C200110051.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110051/C200110051.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110052',
        'C:/controls/stxm-data/guest/0110\C200110052\C200110052.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110052/C200110052.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110052/C200110052.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110053',
        'C:/controls/stxm-data/guest/0110\C200110053\C200110053.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110053/C200110053.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110053/C200110053.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110054',
        'C:/controls/stxm-data/guest/0110\C200110054\C200110054.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110054/C200110054.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110054/C200110054.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110055',
        'C:/controls/stxm-data/guest/0110\C200110055\C200110055.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110055/C200110055.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110055/C200110055.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110056',
        'C:/controls/stxm-data/guest/0110\C200110056\C200110056.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110056/C200110056.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110056/C200110056.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110057',
        'C:/controls/stxm-data/guest/0110\C200110057\C200110057.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110057/C200110057.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110057/C200110057.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110058',
        'C:/controls/stxm-data/guest/0110\C200110058\C200110058.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110058/C200110058.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110058/C200110058.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110059',
        'C:/controls/stxm-data/guest/0110\C200110059\C200110059.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110059/C200110059.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110059/C200110059.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110060.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110060.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110060.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110061',
        'C:/controls/stxm-data/guest/0110\C200110061\C200110061.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110061/C200110061.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110061/C200110061.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110062.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110062.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110062.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110063.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110063.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110063.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110064.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110064.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110064.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110065.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110065.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110065.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110066.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110066.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110066.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110067.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110067.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110067.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110068.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110068.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110068.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110069.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110069.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110069.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110070.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110070.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110070.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110071.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110071.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110071.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110072.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110072.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110072.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110073.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110073.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110073.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110074.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110074.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110074.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110075.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110075.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110075.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110076.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110076.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110076.hdf5',
        'C:/controls/stxm-data/guest/0110\C200110077.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110077.hdf5',
        'C:/controls/stxm-data/guest/0110/C200110077.hdf5']

    for f in flst:
        print('parsing [%s]' % f)
        print(get_file_path_as_parts(f))

__all__ = ['loadDatTo2DArray', 'loadDatToXY', 'getColNumAndItem', 'loadDatToArray']
