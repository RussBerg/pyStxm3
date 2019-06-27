

def create_img_idx_map(spid=0, gt_roi={'SETPOINTS': [-2,2]}, numE=4, numEPU=2):

    img_idx_map = {}
    indiv_img_idx = 0
    #spid = list(self.sp_rois.keys())[0]
    pol_lst = []
    ttl_num_entrys = len(gt_roi['SETPOINTS']) + numEPU
    entry_lst = ['entry%d'%i for i in range(ttl_num_entrys)  ]
    entry_idx = -1
    offset = 0
    for gt_sp in gt_roi['SETPOINTS']:
        #entry_idx += 1
        pol_lst = []
        for i in range(numE):
            for k in range(numEPU):
                img_idx_map['%d' % indiv_img_idx] = {'e_idx': i, 'pol_idx': k, 'sp_idx': 0, 'sp_id': spid,
                                  'entry': 'entry%d' % (k + offset), 'rotation_angle': gt_sp}
                indiv_img_idx += 1
        offset += 2

    return(img_idx_map)

def gen_gt_points(num_gt, num_ev, num_pol):
    lst = []
    offset = 0
    for g in range(num_gt):
        for ev in range(num_ev):
            pol_idx = 0
            for pol in range(num_pol):
                print('%d, %d, %d entry%d' % (g, ev, pol, pol + offset))
        offset += 2

def gen_entry_nms(num_gt, num_ev, num_pol):
    offset = 0
    for g in range(num_gt):
        for ev in range(num_ev):
            for i in range(num_pol):
                print('entry%d'% (i + offset))
        offset += 2
        print ('------------')



if __name__ == '__main__':
    img_idx_map = create_img_idx_map()
    for k, v in img_idx_map.items():
         print(k,v)
    # num_gt = 5
    # num_ev = 3
    # num_pol = 2
    # gen_gt_points(num_gt, num_ev, num_pol)
    # #gen_entry_nms(num_gt, num_ev, num_pol)