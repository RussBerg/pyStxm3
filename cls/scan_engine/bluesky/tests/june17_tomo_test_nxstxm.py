
from suitcase import nxstxm as suit_nxstxm

if __name__ == '__main__':
    from databroker import Broker
    from cls.scan_engine.bluesky.tests.rev_lu_dct import rev_lu_dct
    import simplejson as json

    uids = ['2b5f506e-7826-4616-814f-db4c796b5010', 'eef81630-80dc-4160-ae95-f098fda73585', '9216ecc5-c862-44e1-acef-f2027a45cea4', 'eb8376f5-34fa-4b31-befe-245e6bb8c03d', '8cba7b29-1a25-4c97-90c2-def47943027e']
    first_uid = uids[0]
    last_uid = uids[-1]

    data_dir = r'S:\\STXM-data\\Cryo-STXM\\2019\\guest\\0617'
    fprefix = 'Ctester'
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