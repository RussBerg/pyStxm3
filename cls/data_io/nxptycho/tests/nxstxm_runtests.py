# Tests should generate (and then clean up) any files they need for testing. No
# binary files should be included in the repository.
import os
import simplejson as json
from nxstxm_validate import validate_file
from suitcase.nxstxm import export, finish_export


example_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'example_data')
test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'test_results')

def do_export(scan_json_file, first_uid=None):
    # Exercise the exporter on the myriad cases parametrized in example_data.
    documents = example_data(scan_json_file)
    export_file_prefix = scan_json_file.replace('.json','')
    test_fpath = os.path.join(test_data_dir, export_file_prefix + '.hdf5')
    if(os.path.exists(test_fpath)):
        os.remove(test_fpath)

    doc_keys = list(documents.keys())
    if(first_uid is None):
        first_uid = doc_keys[0]

    if(first_uid in doc_keys):
        first_doc = documents[first_uid]
        export(first_doc, test_data_dir, file_prefix=export_file_prefix, first_uid=first_uid)
        del(documents[first_uid])
        #now process the rest if there are any
        for uid, docs in documents.items():
            export(docs, test_data_dir, file_prefix=export_file_prefix, first_uid=first_uid)

    else:
        print('first_uid[%s] does not exist in documents' % first_uid)

    # For extra credit, capture the return value from export in a variable...
    # artifacts = export(documents, tmp_path)
    # ... and read back the data to check that it looks right.
    finish_export(test_data_dir, export_file_prefix, first_uid)
    result = validate_file(test_fpath)
    assert result == True

def example_data(example_json_fname):
    fpath = os.path.join(example_data_dir, example_json_fname)
    with open(fpath) as json_data:
        js_d = json.load(json_data)
        docs = json.loads(js_d)
    return(docs)


if __name__ == '__main__':

    if(not os.path.exists(test_data_dir)):
        os.mkdir(test_data_dir)

        # detector_image
        # uids = ['0496577b-ceb8-4c3f-b663-d2dc5e3a0c33']

        # osa
        # uids = ['ba182d12-5e2b-4ceb-9a38-396dcaf00640']

        # osa_focus
        # uids = ['7cc1294f-e68f-4163-b38b-29ce26b06830']

        # COARSE IMAGE
        # uids = TODO

        # coarse Goni
        # uids = ['0059e0f9-c685-4b81-801f-efbacd581fac']

        # sample_image
        # uids = ['bb97d213-029b-4300-ac9a-9f5036beafdb']

        # sample image stack
        # uids = ('cbb39dd0-2d7b-4409-8ac9-9db19d4c9ad1', '6a2ed3f7-22ab-4cf1-af26-bb4ad8fa3894',
        #         '8f57201f-65b1-4363-b7a4-97bfe0f2708f')

        # tomo stack data
        # uids = ['0bcef594-0ec9-40b0-857c-13fa79bee2d3', 'a72a9c59-20d2-4f3d-8457-f188a76e96d6',
        #     '33ccce5c-dc49-4c9e-bd34-15c64aec70bf', '727d8351-a3a9-4878-85e2-0beb3b20ebda',
        #     '57770c02-0974-4aef-99c0-a1d27156eaf7', '69e8848e-d132-4cbe-abe1-ee0ce1ca9145']

        # sample_focus
        # uids = ['e9fea907-781f-4ce4-918e-0b404817334c']

        # SAMPLE_POINT_SPECTRA
        # uids = ['343a0683-04fa-4391-a854-cb19672be6e6']

        # line scan
        # uids = ['f31df4d7-f5e5-408a-bf94-eaea54e44fe3']

        # positionr/generic scan
        # uids = ['e280d723-57b2-426e-a3e3-e07012375202']

    #do_export(test_data_dir, example_data_docs)

    do_export('COARSE_GONI_SCAN.json')
    do_export('DETECTOR_IMAGE.json')
    do_export('GENERIC_SCAN.json')
    # do_export('OSA_FOCUS.json')
    # do_export('OSA_IMAGE.json')
    # do_export('SAMPLE_FOCUS.json')
    # do_export('SAMPLE_IMAGE.json')
    # do_export('SAMPLE_IMAGE_STACK.json', first_uid='cbb39dd0-2d7b-4409-8ac9-9db19d4c9ad1')
    # do_export('SAMPLE_LINE_SPECTRA.json', first_uid='f31df4d7-f5e5-408a-bf94-eaea54e44fe3')
    # do_export('SAMPLE_POINT_SPECTRA.json', first_uid='343a0683-04fa-4391-a854-cb19672be6e6')
    # do_export('TOMOGRAPHY_SCAN.json', first_uid='69e8848e-d132-4cbe-abe1-ee0ce1ca9145')