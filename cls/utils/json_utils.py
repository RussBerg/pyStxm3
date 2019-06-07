import simplejson as json
from cls.data_utils.jsonEncoder import NumpyAwareJSONEncoder

def dict_to_json(dct):
    j = json.dumps(dct, sort_keys=True, indent=4, cls=NumpyAwareJSONEncoder)
    return(j)

def json_to_dict(_str):
    dct = json.loads(_str)
    return(dct)


def json_to_file(fpath, js):
    with open(fpath, 'w') as outfile:
        json.dump(js, outfile)

def file_to_json(fpath):
    with open(fpath) as json_data:
        d = json.load(json_data)
        return(d)
    return({})
