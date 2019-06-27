
from suitcase import nxstxm as suit_nxstxm

if __name__ == '__main__':
    from databroker import Broker
    from . rev_lu_dct import rev_lu_dct, img_idx_map

    uid = '245f4646-d1dd-4357-96c5-dcb27c5d5fc6'
    data_dir = r'S:\\STXM-data\\Cryo-STXM\\2019\\guest\\0612'
    fprefix = 'Ctester'
    db = Broker.named('mongo_databroker')
    header = db[uid]
    primary_docs = header.documents(fill=True)
    suit_nxstxm.export(primary_docs, data_dir, file_prefix=fprefix, index=0,
                       rev_lu_dct=rev_lu_dct, img_idx_map=img_idx_map, \
                       first_uid=uid, last_uid=uid)

