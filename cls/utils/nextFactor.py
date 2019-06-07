
"""
Created on 2011-02-22
@author: bergr
"""

def nextFactor( high, low):
    """
    nextFactor:
    Takes a high value and a low value and finds the lowest common factor
    between the two and returns the scalar with which to modify each to be 
    that common factor:
    
    def example():
    xScaler,yScaler = nextFactor(220,50) 
    print 'Ex: '
    print 'to find out how much 220(x) and 50(y) need to be scaled in order to '
    print 'both reach the lowest common factor call nextFactor(220,50)'
    print '    xScaler, yScaler = nextFactor(220,50)'
    print '    xScaler = %d so %d * 220 = %d' % (xScaler, xScaler, xScaler*220)
    print '    yScaler = %d so %d * 50  = %d' % (yScaler, yScaler, yScaler*50)
    """
    i = -1*high
    res = 1
    while res:
        i += high
        res = (high+i) % 4
        #print 'checking %f = %f' % (float(high+i), float(res))
     
        if(res == 0):
            #check if low divides evenly into the result
            resb = (high + i) % low
            if(resb == 0):
                #print 'this works for low: %f * %f' % (low, (high+i)/low)
                lowFactor = (high+i)/low
            else:
                #keep looking
                res = 1    
        
    #print 'this works for high: %f * %f' % (high, (high+i)/high)
    highFactor = (high+i)/high    
    return (highFactor, lowFactor)

def example():
    xScaler,yScaler = nextFactor(220,50) 
    print('Ex: ')
    print('to find out how much 220(x) and 50(y) need to be scaled in order to ')
    print('both reach the lowest common factor call nextFactor(220,50)')
    print('    xScaler, yScaler = nextFactor(220,50)')
    print('    xScaler = %d so %d * 220 = %d' % (xScaler, xScaler, xScaler*220))
    print('    yScaler = %d so %d * 50  = %d' % (yScaler, yScaler, yScaler*50))
    
    
    

if __name__ == '__main__':
    x,y = nextFactor(220,50) 
    print(x,y)
    