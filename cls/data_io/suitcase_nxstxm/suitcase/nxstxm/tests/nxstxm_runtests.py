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
        #js_d = json.load(json_data)
        #docs = json.loads(js_d)
        docs = json.load(json_data)
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
        #uids = ['0952a447-f559-474c-b98c-497eee9902ff', '45bf80c2-bed1-47bd-acc9-8d166240ec21', '7aef74dd-dff2-4b37-ab97-85db7fc50ff1', '8700b556-e4fe-4234-98f3-78717295b68d', 'b5a09bcf-a738-48fa-b327-ca484c6a5e3f', 'ef8dec71-e742-4a79-99d5-d74a1ada2ecd', '9a356ac0-50a1-4b71-85e9-813958897d97', '3cf75824-7c9b-4089-be76-4fe513148766', '7d76f034-e435-4789-8444-de880461f749', '175fe802-6ab6-4caf-a6d0-7002a4df6b01', '4ff1b320-15ec-4cff-9572-7e9935236f8d', 'fef767b6-d014-41d2-9e87-1dbcf9a678a1', 'f177d8fe-db7c-4b17-ad8d-802bd760df47', '13e6abf1-6872-41e3-8735-0349459c71d2', 'fa8dc345-8ab5-41e3-b4d5-c01998b0141d', '3ca5168e-61d9-45df-9b80-3b49fe5214ab', '61467363-2ee0-4c1f-b598-c06c57b52525', '0fde1256-7936-464f-8894-61dee9cc3ce7', '050c8ab0-7786-4d94-85f6-b6527a9167f1', 'd2d575ce-adb4-425c-bd8c-c2d7f6fc33bb', '0a24c733-b68a-4e8a-a232-9d53930681cc', '970af9b9-2fb9-471a-9f54-49e3390de607', '2f037042-d43a-4333-b467-0c2654d3bd0e', '10fc2bb0-ebd5-4c2e-b79e-274d216fc2fe', '4eaa286d-7505-4223-a5b6-ea805227d015', '78001795-51de-46c2-9cc3-a01132eca784', '04f468aa-2a6f-4d29-bcf7-23cb92ffa5a3', '60750a25-08c6-46cf-859c-2003ed8cf801', 'a7c9f5aa-c809-4a11-9ede-417c6ababae6', '8509d1a7-ba45-476b-8fcd-f6d4739bdd52', 'fee2f7e7-2600-455e-bb66-b8c793ef3d89', 'ae2501ce-4539-43ea-8d85-e875e37f19aa', '8350ea42-6a29-4f70-b712-d3541366357b', 'cc0a63b5-fde6-4fd1-ac2c-7151491bda50', '247b69ec-161a-4680-9be8-437bdc3b2204', 'dc2b881b-e258-4dc0-836e-d72b3d56f128', 'da1e0eb0-f7b3-4cc8-8d51-01d68e650c18', 'f6f34f4f-b425-426b-8b0f-dae296cdc8d7', 'd21d1914-da00-4d1c-8deb-2bab8f04def1', '430d53d1-b265-4fc1-8670-daa6d4b86404', 'f7279bb7-7d90-4bd8-aa84-34e217c40f59', '3c27bd06-b314-4d5a-889a-cad55a9ac0c8', 'fbf59824-09e5-4292-b0c7-c7d047936e4c', '1e72850e-ffea-4c81-a1e4-fe863ab97d8e', '2858717e-1dd3-481a-881c-ce7c0b6bd855', 'd2cb70de-2484-4402-a051-9972c6e8a9ce', '1aecf0c8-6b35-4ba4-835c-a814e38912a0', 'c3204f57-522e-468f-9bc3-38180cfe331f', 'b38251f7-2ab4-4a9c-9a73-3a4fe28fdbc7', '7af89989-2f46-44d9-99ec-81b0d7994780', '682fa1ab-1cb6-4e18-8280-6ab9bca2cf60', 'daaa045c-e198-49b4-99ed-ad4d1cae4276', 'a91235b5-0d20-4f70-b03b-65f3841063aa', 'db9846cb-c97f-43ae-b1bb-45b4233559e1', 'cc158a82-7833-4f02-978d-9a4a76a8175d', '0b180f10-b865-4afe-be0f-bd07f7516799', '3c80d516-d9b8-4da2-8413-d10849e6f4de', 'bd340710-f90e-4716-99d8-8e0ea58d5c5a', '605ad10b-421d-42d7-afee-9b27288dc7c6', 'af4b6860-2152-4f42-a17e-2adc084c9b29', '2b3fcb86-ffab-4179-8a5d-6d39e9ab7670', '4dc0d4e8-a083-4c0d-a5ca-b437d381f7ea', '7c1e6fe5-a3d4-4d6a-981d-685cea7f38c8', '5d413d7a-d6fb-41b8-8c99-a5472f124171', 'eb5a1769-25ac-4438-9c3d-aa81b0f63d3e', 'c884886d-90b3-4d1b-9a82-f6a7cb2040d8', 'a8d64920-2d52-4574-a2ad-e0bf230d4551', 'f837edfa-27ee-47a0-a69c-2887a78a3c32', 'e9eb8217-005f-4d03-9c7b-5d143428b933', 'cd7b8654-e042-46f9-a5f5-de0fb2ea167a', '3167d07e-e5cc-416d-9343-6af759ecfb56', '20415f6b-be46-44ca-b76e-be72ef6cf27f', 'd75d35c0-0b94-4897-aaa6-032570f732bf', '94d8c37c-1fb9-4646-875b-a503c3607ad9', '3f672275-fcf5-4c31-8401-24f4e4defb52', '43526236-ad76-466a-ad0e-f9829e687e63', '301bf5ed-3e44-4126-b27f-dcc45b8bb3a1', 'd3143963-5e3b-4f3f-a94b-fdd241550af0', 'ed754032-c8e9-4386-8022-381d9342d9f1', 'c171fd0a-3b92-4c30-86bf-f9af42892e02', 'd00066a2-1874-4d9a-bf65-4db0017ecc28', '8115e587-73c1-4c1c-b0b6-622db23ad48b', '31aed9cb-3ef4-45c3-b1b9-4f7484230bfa', 'a36325bb-ba43-4489-8ef8-c5f59662ed1e', 'ce00d65f-24e8-46a9-9d26-e1cbf266a1f3', 'aed6b4dd-9075-4880-b49d-e28c45b890f0', '98210d38-bc61-4d74-b24e-234d51f2320b', '04589ab2-9dc5-410a-bf9d-22bc7a8d22fb', 'a447c850-f016-4067-a555-c3f0a4cf5411', '25168b4e-9b2d-4fde-adf7-ae28e5132569', '9ecacbde-61c7-4281-b3c2-39b3a3d5ec72', '6f58f283-7683-4bda-98cc-93c5bd3648bf', '96e9f7fa-069a-44d5-9440-469d145a424f', 'dbf69e25-bc9c-4709-8f70-cccdd34086a8', 'ada93763-7fcc-4d2a-b19a-ef965bf65110', '25f09a3c-01f5-4709-9138-37d20d8aaf9e', 'b2ffd8e6-3cd0-4cf9-9fa8-e6e3575f7ac5', '33f5d874-2c7f-4063-ab39-adca4f53cfbb', '56a6f930-5a16-4683-aabe-1092e6de3ef7', '76f42821-f746-4c36-a86c-42c5a10d4c86', '72e505ee-0e6f-4550-90da-598844fee270', '6e1a2269-edcf-4a2b-98d0-ea4113d145e9', '39835317-92f3-4608-991d-3a8a90e9da2e', 'd4fd5c25-0c4c-472f-bc09-5b075180b669', '403a2834-26e3-4b3b-b237-67012370fd3e', 'acde1eed-a9f9-49d0-ae60-d52cd997fdf1', '47af3034-1429-48ed-9edd-923be34d26fb', '0e3ec907-7fc7-4fa5-84af-beac8b29eebc', '1611ef93-738b-4eb3-b79d-a3634644651c', '524f9ada-ee21-4da5-b46a-d71223509d21', 'd6102c1b-6d37-4de8-9cbb-0b78a1326e8e', '8ee903d0-247c-4fc3-8f9e-4a3c020ae49e', '85461991-c822-43a1-b37a-0ad9bbd567fa', '90c36389-d636-45c0-bd15-e4cdbd436f37', '20343c4d-066e-4e0f-b36e-fc10dc1f819c', 'be27796e-12ce-4110-a730-be19bd5eed4e', 'dc986d13-6a90-45b9-b722-fb2a7cde9450', 'b1f18362-2964-45df-98b1-4215d478b1dd', 'c381c55c-e044-4069-94ab-4eaaea418e01', '396cfe66-b731-43ca-bf90-e6ab2331104f', 'ce117999-14ee-4751-bf95-b34ca5ef8375', 'ebd9f3ab-1b0e-46ae-bf7c-2ebd74aa5e17', '2de83ffe-33f3-45eb-b3b8-93e646cd9265', 'ffba74f0-c9eb-4022-a0bc-4f70fa07e908', 'eb8480a4-2c44-4ba0-8a81-07a75ebb0b2a', '49188256-cd67-4854-9314-852c5c18cf69', '761ced4d-ed8a-4af3-b83f-3b18e3c4da31', 'a914a455-353e-4c77-b49d-5180976172cb', '3cc123cc-d49a-4ed4-82ae-94b0d72e51c3', '02dd93ff-49cc-4f13-99df-76244f24ee97', 'b59c121d-b613-4c79-bad7-1cdebf77c80e', '3e209b0c-1428-4825-b6a0-a7d0c3cb7a7f', '1bd1bd89-ef2c-4bb2-ba51-cafbda9f64bb', '31a3d61c-d536-4719-b430-81861e4b30bc', '45676e15-36b4-4071-b0ab-d11cf2820364', 'd7e152d1-d354-4778-8135-e92a0d8d351e', 'cabf704d-a556-479a-a549-479e5947362c', '8f714421-dce3-46da-b12d-2d25cd79136d', '0093759a-e62e-4ff9-9c05-27ae9b15e459', '665d646d-149e-4876-81db-f2a811e1a3d7', '553f485e-9ccb-43ce-b356-3b98d941e2e5', '6535ed31-ae42-4535-bb9a-c4e241d8e908', '340e3ce9-09b2-4dca-8f93-5d5293d4cd4b', '8ea7cceb-8325-40d5-b2b1-18b7ed5256ab', '8002074d-35d5-4a98-88f8-50b6fee39220', '6936e16c-ad5d-4cab-9502-0f99bae42433', 'bc86aaef-e7a6-4440-9ba9-e1e96eb8a1eb', '10a06eb1-7710-4326-ba7c-68ee68c27e56', 'bcc9d493-dbfe-46c0-8da9-11c5d65dc87c', 'd9da1cd1-b498-438b-9b9d-6ba3a51a5eb0', 'cda23853-7043-461e-80c8-2a332379efa5', 'b6089a94-8045-48f2-9e64-4e05967db666', '8aea5d81-0de6-41d7-af50-ae5ca1034e4e', '3b206309-a6f1-4e63-bd58-78731c0ec800', '026ce596-a697-4eaf-a0d3-2d39342664c2', '7be6822d-9258-4e75-9866-6b653f5c5977', 'e7d5158d-0f0e-40ef-ae7b-7489b9aa221e', '785a547e-b555-45fc-b081-8752da36cd97', 'a87a22f8-f6fa-4ac9-bf2b-312bd06c7cca', '074f3f3d-64b0-4a33-8f60-fc177c872e70', '8ec820dc-709b-499c-a5d0-9400aeb9659d', '337b7923-2673-402f-8bb2-61bf90f8208b', '30b1cdfd-a85b-4d92-adf8-35f764b114c6', '378014d7-3d23-4294-9ecf-dfb5db985007', '06be8a37-0213-4f77-963a-6e73d56bd64e', 'c5ff189a-fa96-4cab-9468-77d11725ef0a', 'f1fcac0f-7f95-42d8-b3df-f5f4f1e558b5', '336adaed-56e2-4777-a75d-1b42c9a37daa', '74fa3204-ad79-45df-8e36-5c3b826b3ff1', '1634108d-bf43-4c5f-acc7-4fb79c6448f8', 'aeec1009-b8c8-47c1-8017-aaa17d14b8e6', '0eaf4f91-3fd2-4e62-9ba5-3dfc388e666d', 'cff1a633-2851-4941-835c-df9a00625e27', '58cfa5e1-1cc2-4995-8b23-548bacc04103', '958a56bd-c83e-4329-aa5f-7953677590bd', 'a75f92c6-bd1a-48b0-a0c0-565692020f2b', 'b8b31f7c-f2d8-4e5c-96e7-8f061d194952', '53ba7c50-5ff1-4ad7-9764-2cbd3ab82436', 'c1a812bf-5cbb-4b7c-ba6b-d4bf1d03a75e', '6f5f026a-7745-4887-bc4e-10d8a0489ec2', '70e840e4-eab7-424b-903b-cd9f5d99da71', 'd592f577-bbc0-4214-9434-988f3f5c807b', '9b25bb1f-d032-40bb-b2c4-c51de6077562', '2d1a03d4-fc50-44ae-8e3b-bb7ca5fb2f74', '86c24f17-d584-4e76-b32c-fb703a1333c0', '39749ad7-a15e-4dbc-9619-705da23c75fd', '462978a5-945b-4784-93ee-b523dc744cd1', 'afa6b078-ae7d-4688-9659-9d07ee060986', '6c8d070f-cd7b-4ebf-8cd7-0bfa0808ea11']

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

    #do_export('COARSE_GONI_SCAN.json')
    #do_export('DETECTOR_IMAGE.json')
    #do_export('GENERIC_SCAN.json')
    # do_export('OSA_FOCUS.json')
    # do_export('OSA_IMAGE.json')
    # do_export('SAMPLE_FOCUS.json')
    #do_export('SAMPLE_IMAGE.json')
    #do_export('SAMPLE_IMAGE_STACK.json', first_uid='cbb39dd0-2d7b-4409-8ac9-9db19d4c9ad1')
    do_export('SAMPLE_IMAGE_STACK.json', first_uid='6c8d070f-cd7b-4ebf-8cd7-0bfa0808ea11')

    # do_export('SAMPLE_LINE_SPECTRA.json', first_uid='f31df4d7-f5e5-408a-bf94-eaea54e44fe3')
    # do_export('SAMPLE_POINT_SPECTRA.json', first_uid='343a0683-04fa-4391-a854-cb19672be6e6')
    # do_export('TOMOGRAPHY_SCAN.json', first_uid='69e8848e-d132-4cbe-abe1-ee0ce1ca9145')