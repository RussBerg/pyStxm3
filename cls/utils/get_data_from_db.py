import os
import simplejson as json
import numpy as np
import datetime
from databroker import Broker
from suitcase.nxstxm.stxm_types import scan_types


class NumpyAwareJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # try:
        # print type(obj)
        if isinstance(obj, np.ndarray) and obj.ndim == 1:
            return obj.tolist()
        elif isinstance(obj, np.ndarray) and obj.ndim == 2:
            return obj.tolist()
        elif isinstance(obj, np.ndarray) and obj.ndim == 3:
            return obj.tolist()
        elif isinstance(obj, np.generic):
            return obj.item()
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, datetime.date):
            str = obj.isoformat()
            # str = unicode(str, errors='replace')
            str = str(str, errors='ignore')
            return str
        else:
            return json.JSONEncoder.default(self, obj)

        # except TypeError:
        #    _logger.debug('dataRecorder.py: NumpyAwareJSONEncoder: TypeError')


def get_scan_type_str(scan_type):
    for i in range(len(scan_types)):
        if(scan_type is i):
            return(str(scan_types(i)).replace('scan_types.',''))
    return(None)


def get_docs_from_databroker(uids):
    '''
    get the data using the uids that were passed and save it as a json string on disk, to be used to create example
    data used for tests

    uids = ['79d87128-7ac1-4da0-a683-ffdf2ddbb380', 'ef92aeb9-33d3-47c5-be79-057ac09dc98d', 'f06ffeb1-4e25-41e9-be5e-5cc6f17146ad', 'a4f34698-4cc8-49c3-b330-69762a91a81c', '562da7a6-9f94-408f-b3f2-f887d55f4955', '1f7f26a6-adf6-4635-9eca-0c25bf1d089c']

    :param uids:
    :return:
    '''
    dct = {}
    db = Broker.named('mongo_databroker')
    for uid in uids:
        print('starting basic export [%s]' % uid)
        header = db[uid]
        docs = header.documents(fill=True)
    return(docs)


def get_docdata_from_databroker(uids, as_dict=False):
    '''
    get the data using the uids that were passed and save it as a json string on disk, to be used to create example
    data used for tests

    uids = ['79d87128-7ac1-4da0-a683-ffdf2ddbb380', 'ef92aeb9-33d3-47c5-be79-057ac09dc98d', 'f06ffeb1-4e25-41e9-be5e-5cc6f17146ad', 'a4f34698-4cc8-49c3-b330-69762a91a81c', '562da7a6-9f94-408f-b3f2-f887d55f4955', '1f7f26a6-adf6-4635-9eca-0c25bf1d089c']

    :param uids:
    :return:
    '''
    dct = {}
    db = Broker.named('mongo_databroker')
    for uid in uids:
        print('starting basic export [%s]' % uid)
        header = db[uid]
        md = json.loads(header['start']['metadata'])
        _img_idx_map = json.loads(md['img_idx_map'])
        # img_idx_map[uid] = copy.copy(_img_idx_map['%d' % 0])
        primary_docs = header.documents(fill=True)
        dct[uid] = list(primary_docs)
        scan_type_str = get_scan_type_str(md['scan_type'])
        print('Saving [%s]' % scan_type_str)

    docs = json.dumps(dct, sort_keys=True, indent=4, cls=NumpyAwareJSONEncoder)
    if(as_dict):
        return(scan_type_str, dct)
    else:
        return(scan_type_str, docs)

def save_doc_data(fpath, docs):
    with open(fpath, 'w') as outfile:
        json.dump(docs, outfile)


if __name__ == '__main__':
    example_data_dir = r'C:\controls\git_sandbox\pyStxm3\cls\data_io\suitcase_nxstxm\suitcase\nxstxm\tests\example_data'

    #detector_image
    #uids = ['b2673825-c67b-4fb4-91af-38133506b838']

    #osa
    #uids = ['92b4e825-6007-4c00-af1d-f97b156dad43']
    #
    # #osa_focus
    #uids = ['d9ea70fb-1535-4285-bb48-bf4fe80bbba6']
    #
    # #COARSE IMAGE
    # # uids = TODO
    #
    # #coarse Goni
    #uids = ['87b8e207-3641-4419-83ad-b7b48f9c794f']
    #
    # # sample_image
    # uids = ['8b8a62f3-f0c6-4418-adf6-f9ce4dc3b12e']

    #sample image stack
    #uids = ('cbb39dd0-2d7b-4409-8ac9-9db19d4c9ad1', '6a2ed3f7-22ab-4cf1-af26-bb4ad8fa3894', '8f57201f-65b1-4363-b7a4-97bfe0f2708f')

    # tomo stack data
    # uids = ['0bcef594-0ec9-40b0-857c-13fa79bee2d3', 'a72a9c59-20d2-4f3d-8457-f188a76e96d6',
    #     '33ccce5c-dc49-4c9e-bd34-15c64aec70bf', '727d8351-a3a9-4878-85e2-0beb3b20ebda',
    #     '57770c02-0974-4aef-99c0-a1d27156eaf7', '69e8848e-d132-4cbe-abe1-ee0ce1ca9145']

    # sample_focus
    #uids = ['224df41b-94f7-487f-9327-b8a4e06a6de2']

    # SAMPLE_POINT_SPECTRA
    #uids = ['343a0683-04fa-4391-a854-cb19672be6e6']

    #line scan
    #uids = ['f31df4d7-f5e5-408a-bf94-eaea54e44fe3']

    #positionr/generic scan
    #uids = ['5dc79ce7-e6fd-4ab8-b0b5-69df9c84d432']
    #uids = ['e280d723-57b2-426e-a3e3-e07012375202']

    #scan_type_str, docs = get_docdata_from_databroker(uids)
    #print(docs)
    #save_doc_data(os.path.join(example_data_dir, scan_type_str + '.json'), docs)
    #docs = get_docs_from_databroker(['cbb39dd0-2d7b-4409-8ac9-9db19d4c9ad1'])
    #print(docs)

    #uids = ['eba21360-1f53-485b-927e-a8257d410373', '2ba10d20-69bd-4c1e-9796-037204b30db7', 'f784a26a-5aeb-472c-9fcf-939b3b613639', '4b3ff219-1a54-4df2-9d6f-7fa004bae993', 'c8c86628-4fe3-4c40-95f4-0e092be76975', 'f0df13a6-4dd7-46bd-b59b-fb13072166f3', 'f4e10859-e82b-4ee5-a17a-f80256ac9fd1', '02c4c7be-b944-49b7-8e5c-2b4b976b610c', 'c1b88491-de32-458d-bc47-bd571758416b', 'a32087f9-195e-4280-b725-8a6092ff7700']

    #1520 x 160
    uids = ['37e290a0-b8c8-4078-b033-7bb760b6b933']
    #80 x 160
    #uids = ['ac4d47ad-c473-4944-99db-0178fed66934']
    scan_type_str, docs = get_docdata_from_databroker(uids, as_dict=True)
    print(docs)