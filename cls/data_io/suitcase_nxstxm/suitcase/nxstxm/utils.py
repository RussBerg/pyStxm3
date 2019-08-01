










'''
Created on 2014-09-03

@author: bergr
'''
def dct_put(d, keys, item, overwrite=True):
    '''
    dct_put: is a function that accepts a . separated string that represents the levels of a dict.
     It makes it clean to access multi level dictionaries within code because predefined strings used as standard
     throughout the rest of the code.
    Example:
        dct_put(main, 'SCAN.DATA.DETECTORS', [])
        creates the following dictionary in the dict main, main['SCAN']['DATA']['DETECTORS']
        and assigns it to equal an empty list (in this case).

    Example: use defined dict strings:
        #define the strings in a separate shared module
        SCAN_DATA_DETECTORS = 'SCAN.DATA.DETECTORS'
        ...

        dct_put(main, SCAN_DATA_DETECTORS, [])


    :param d: dictionary to put the value passed into
    :type d: dictionary

    :param keys: a "." separated string used as keys for the dict
    :type keys: a "." separated string  such as 'DATA.SCAN1.POINTS'

    :param item: item to assign
    :type item: any valid python variable

    :param overwrite: If key already exists in dictionary allow it to be over written or not (True is default)
    :type overwrite: bool

    :return: Nothing
    '''
    try:
        if "." in keys:
            key, rest = keys.split(".", 1)
            if key not in d:
                d[key] = {}
            dct_put(d[key], rest, item, overwrite)
        else:
            if(keys in list(d.keys())):
                #if the key exists only overwrite val if flag is True
                if(overwrite):
                    d[keys] = item
            else:
                #key is new so create it
                d[keys] = item
    except KeyError:
        #raise
        return(None)

def dct_get(d, keys):
    '''
    dct_get: is a function that accepts a . separated string that represents the levels of a dict.
     It makes it clean to access multi level dictionaries within code because predefined strings used as standard
     throughout the rest of the code.
    Example:
        dct_get(main, 'SCAN.DATA.DETECTORS')
        returns the following from the dictionary main, main['SCAN']['DATA']['DETECTORS']

    Example: use defined dict strings:
        #define the strings in a separate shared module
        SCAN_DATA_DETECTORS = 'SCAN.DATA.DETECTORS'
        ...

        detector_lst = dct_get(main, SCAN_DATA_DETECTORS)


    :param d: dictionary to put the value passed into
    :type d: dictionary

    :param keys: a "." separated string used as keys for the dict
    :type keys: a "." separated string  such as 'DATA.SCAN1.POINTS'

    :return: The item located in the dictionary path given in the keys param
    '''
    try:
        if "." in keys:
            key, rest = keys.split(".", 1)
            return dct_get(d[key], rest)
        else:
            if(keys in list(d.keys())):
                return d[keys]
            else:
                return(None)
    except KeyError:
        #raise
        return(None)