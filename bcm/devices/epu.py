'''
Created on Jun 16, 2016

@author: bergr
'''

# def convert_polarity_int_to_str(p):
def convert_wrapper_epu_to_str(p):
        '''
                        -1                1        0            -2                2        3?
        cbox.addItems(['CircLeft','CircRight','LinHor', 'IncVert-', 'IncVert+','LinInc'])
                        0
        cbox.addItems(['CircLeft','CircRight','LinHor', 'IncVert-', 'IncVert+','LinInc'])
         
        '''
        if(p <= 0):
            return('CircLeft')
        elif(p == 1):
            return('CircRight')
        elif(p == 2):
            return('LinHor')
        elif(p == 3):
            return('IncVert-')
        elif(p == 4):
            return('IncVert+')
        elif(p == 5):
            return('LinInc')
        else:
            return('UnknownPolarity')    

# def convert_wrapper_epu_to_str(val):
#         #cbox.addItems(['CircLeft','CircRight','LinHor', 'IncVert-', 'IncVert+','LinInc'])
#         strs = ['CircLeft','CircRight','LinHor', 'IncVert-', 'IncVert+','LinInc']
#         #return(strs[val])
#     
#         if(val == -1):
#             return(strs[1])
#         if(val == 0):
#             return(strs[0])
#         if(val == 1):
#             return(strs[2])
#         if(val == 2):
#             return(strs[3])
#         if(val == 3):
#             return(strs[4])
#         if(val == 4):
#             return(strs[5])
#         else:
#             return(strs[0])        
                

if __name__ == '__main__':
    pass