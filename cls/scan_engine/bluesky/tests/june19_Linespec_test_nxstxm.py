
from suitcase import nxstxm as suit_nxstxm

if __name__ == '__main__':
    from databroker import Broker
    from cls.scan_engine.bluesky.tests.rev_lu_dct import rev_lu_dct
    import simplejson as json
    from cls.utils.file_system_tools import get_next_file_num_in_seq

    #uids = ['6d5cf42b-ad8c-41ca-9cb1-404e0b004a5c']
    uids = ['b7f811e4-01c6-419a-b2b0-98aed642d42b']
    first_uid = uids[0]
    last_uid = uids[-1]

    data_dir = r'S:\\STXM-data\\Cryo-STXM\\2019\\guest\\0619'
    fprefix = 'C' + str(get_next_file_num_in_seq(data_dir, prefix_char='C', extension='hdf5'))
    db = Broker.named('mongo_databroker')
    # for uid in uids:
    #     header = db[uid]
    #     primary_docs = header.documents(fill=True)
    #     suit_nxstxm.export(primary_docs, data_dir, file_prefix=fprefix, index=0,
    #                        rev_lu_dct=rev_lu_dct, img_idx_map=img_idx_map, \
    #                        first_uid=uid, last_uid=uid)
    idx = 0
    for uid in uids:
        print('starting basic export [%s]' % uid)
        header = db[uid]
        md = json.loads(header['start']['metadata'])
        _img_idx_map = json.loads(md['img_idx_map'])
        #img_idx_map[uid] = copy.copy(_img_idx_map['%d' % 0])
        primary_docs = header.documents(fill=True)
        suit_nxstxm.export(primary_docs, data_dir, file_prefix=fprefix, index=0, rev_lu_dct=rev_lu_dct, \
                      img_idx_map=_img_idx_map['%d' % idx], first_uid=first_uid, last_uid=last_uid)
        idx += 1

    suit_nxstxm.finish_export(data_dir, fprefix, first_uid)