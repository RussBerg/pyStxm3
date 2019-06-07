
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
