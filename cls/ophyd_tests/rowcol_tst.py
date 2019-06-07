

def factors_of_6(value):
    return value * 6




def update_idxs(seq_num, l):
    '''
    The doc only contains a single sequence number so generate row column indexs
    :param seq_num:
    :return:
    '''
    global x_idx, y_idx, cols

    if(seq_num in l):
        # increment y
        y_idx += 1
        # reset x
        x_idx = 0
    else:
        # increment x
        if(seq_num is not 1):
            x_idx += 1



    print('[%02d] = [%d, %d]' % (seq_num, y_idx, x_idx))

if __name__ == '__main__':
    x_idx = 0
    y_idx = 0
    cols = 5
    l = [item for item in range(1,cols)]
    l2 = [(item*cols)+1 for item in l]

    for i in range(1,26):
        update_idxs(i, l2)