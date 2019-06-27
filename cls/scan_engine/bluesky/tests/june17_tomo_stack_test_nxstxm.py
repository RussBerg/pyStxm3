
from suitcase import nxstxm as suit_nxstxm

if __name__ == '__main__':
    from databroker import Broker
    from cls.scan_engine.bluesky.tests.rev_lu_dct import rev_lu_dct
    from cls.utils.file_system_tools import get_next_file_num_in_seq
    import simplejson as json

    uids = ['008e0080-4628-43a0-ab8b-aea54bc68b72', '90f39c5c-3d2e-4a8f-a78f-c5c605d5242b', 'fdc37aed-dc16-4dbd-9e7f-83a713e3320f', '9e90d217-539a-4dff-bc3b-626cf546f832', 'aca48ca0-2ca8-4302-a773-7ea0c9334831', '972edd54-1099-4f7a-94f3-d0e2f9fdf2a5', '465171bc-a369-495d-9af1-5e7bbcd797b5', '83782177-94ef-4eab-9c91-39cc926b9e67']

    first_uid = uids[0]
    last_uid = uids[-1]

    data_dir = r'S:\\STXM-data\\Cryo-STXM\\2019\\guest\\0618'
    fprefix = 'C' + str(get_next_file_num_in_seq(data_dir, prefix_char='C',extension='hdf5'))
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