'''
Created on 2012-06-01

@author: bergr
'''
class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError


#Animals = Enum(["DOG", "CAT", "Horse"])

#print Animals.DOG