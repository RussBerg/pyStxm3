
def compare_strings(s1, s2):
    '''
    take two strings and compare them then point out what is different about the two
    :param s1:
    :param s2:
    :return:
    '''
    import difflib
    d = difflib.Differ()
    result = list(d.compare([s1], [s2]))
    if(len(result) == 4):
        print('s1: %s' % result[0])
        print('s1: %s' % result[1])

        print('s2: %s' % result[2])
        print('s2: %s' % result[3])
    return(result)















if __name__ == '__main__':
    s1 = 'DW:1.0000RX:8.0000NX:50AR:0.0000LS:0.0500LU:0.0010PS:0.0050PU:0.0000PT:0.0306IT:0.0015DT:0.0000NF1:48.3000NR1:0.0500NBW1:1.0000NF2:68.3600NR2:0.0600NBW2:1.0000SR:1000.0000DFBW:400'
    s2 = 'DW:1.0120RX:8.0000NX:50AR:0.0000LS:0.0500LU:0.0010PS:0.0050PU:0.0000PT:0.0306IT:0.0015DT:0.0000NF1:48.4000NR1:0.0500NBW1:1.0000NF2:68.3600NR2:0.0600NBW2:1.0000SR:5.2340000DFBW:400'
    compare_strings(s1, s2)
    