
from functools import reduce

def sum_lst(lst):
    return(reduce((lambda x, y: x + y), lst))

def prod_lst(lst):
    return(reduce((lambda x, y: x * y), lst))


def merge_to_one_list(lists):
    res_lst = []
    tpl_lst = list(zip(*lists))
    for tpl in tpl_lst:
        for t in tpl:
            res_lst.append(t)
    return(res_lst)


def merge_two_to_one(lista, listb):
    rc = [response for ab in zip(lista, listb) for response in ab]
    return(rc)

def sort_str_list(lst):
    ''' take a list of strings that may contain integers and sort'''
    #lst.sort(key=lambda f: int(list(filter(str.isdigit, f))))
    lst.sort(key=lambda x: int(''.join(filter(str.isdigit, x))))
    return(lst)
