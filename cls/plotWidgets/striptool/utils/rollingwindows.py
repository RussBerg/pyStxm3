'''
Created on May 2, 2012

@author: bergr
'''



import numpy as np




def roll(a, val):
    
    b = a
    sz = b.shape[0]
    c = np.resize(b,(sz+1,))
    c = c[1:]
    c[-1] = val
    return(c)




if __name__ == "__main__":
    a = np.array([1,2,3,4,5])
    b = np.array([1,2,3,4,5,23,54,21,22,23,13,11])
    for num in b:
        a = roll(a, num)
        print(a)
    
    