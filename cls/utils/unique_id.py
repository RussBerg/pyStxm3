'''
Created on 2013-05-17

@author: bergr
'''
import random
from datetime import datetime
import time


def __uniqueid__():
    """
      generate unique id with length 17 to 21.
      ensure uniqueness even with daylight savings events (clocks adjusted one-hour backward).

      if you generate 1 million ids per second during 100 years, you will generate 
      2*25 (approx sec per year) * 10**6 (1 million id per sec) * 100 (years) = 5 * 10**9 unique ids.

      with 17 digits (radix 16) id, you can represent 16**17 = 295147905179352825856 ids (around 2.9 * 10**20).
      In fact, as we need far less than that, we agree that the format used to represent id (seed + timestamp reversed)
      do not cover all numbers that could be represented with 35 digits (radix 16).

      if you generate 1 million id per second with this algorithm, it will increase the seed by less than 2**12 per hour
      so if a DST occurs and backward one hour, we need to ensure to generate unique id for twice times for the same period.
      the seed must be at least 1 to 2**13 range. if we want to ensure uniqueness for two hours (100% contingency), we need 
      a seed for 1 to 2**14 range. that's what we have with this algorithm. You have to increment seed_range_bits if you
      move your machine by airplane to another time zone or if you have a glucky wallet and use a computer that can generate
      more than 1 million ids per second.

      one word about predictability : This algorithm is absolutely NOT designed to generate unpredictable unique id.
      you can add a sha-1 or sha-256 digest step at the end of this algorithm but you will loose uniqueness and enter to collision probability world.
      hash algorithms ensure that for same id generated here, you will have the same hash but for two differents id (a pair of ids), it is
      possible to have the same hash with a very little probability. You would certainly take an option on a bijective function that maps
      35 digits (or more) number to 35 digits (or more) number based on cipher block and secret key. read paper on breaking PRNG algorithms 
      in order to be convinced that problems could occur as soon as you use random library :)

      1 million id per second ?... on a Intel(R) Core(TM)2 CPU 6400 @ 2.13GHz, you get :

      >>> timeit.timeit(uniqueid,number=40000)
      1.0114529132843018

      an average of 40000 id/second
    """
    mynow=datetime.now
    sft=datetime.strftime
    # store old datetime each time in order to check if we generate during same microsecond (glucky wallet !)
    # or if daylight savings event occurs (when clocks are adjusted backward) [rarely detected at this level]
    old_time=mynow() # fake init - on very speed machine it could increase your seed to seed + 1... but we have our contingency :)
    # manage seed
    seed_range_bits=14 # max range for seed
    seed_max_value=2**seed_range_bits - 1 # seed could not exceed 2**nbbits - 1
    # get random seed
    seed=random.getrandbits(seed_range_bits)
    current_seed=str(seed)
    # producing new ids
    while True:
        # get current time 
        current_time=mynow()
        if current_time <= old_time:
            # previous id generated in the same microsecond or Daylight saving time event occurs (when clocks are adjusted backward)
            seed = max(1,(seed + 1) % seed_max_value)
            current_seed=str(seed)
            
        newid=int(''.join([sft(current_time,'%S%f%d%m%Y'),current_seed]))
        # generate new id (concatenate seed and timestamp as numbers)
        #newid=hex(int(''.join([sft(current_time,'%f%S%M%H%d%m%Y'),current_seed])))[2:-1]
        #newid=int(''.join([sft(current_time,'%f%S%M%H%d%m%Y'),current_seed]))
        #newid=int(''.join([sft(current_time,'%S%f%d%m%Y'),current_seed]))
        #newid=int(''.join([sft(current_time,'%S%f%d%m'),current_seed]))
        # save current time
        old_time=current_time
        # return a new id
        yield newid


def __uniqueshortid__():
    mynow=datetime.now
    sft=datetime.strftime
    # store old datetime each time in order to check if we generate during same microsecond (glucky wallet !)
    # or if daylight savings event occurs (when clocks are adjusted backward) [rarely detected at this level]
    old_time=mynow() # fake init - on very speed machine it could increase your seed to seed + 1... but we have our contingency :)
    # manage seed
    seed_range_bits=10 # max range for seed
    seed_max_value=2**seed_range_bits - 1 # seed could not exceed 2**nbbits - 1
    # get random seed
    seed=random.getrandbits(seed_range_bits)
    current_seed=str(seed)
    # producing new ids
    while True:
        # get current time 
        current_time=mynow()
        if current_time <= old_time:
            # previous id generated in the same microsecond or Daylight saving time event occurs (when clocks are adjusted backward)
            seed = max(1,(seed + 1) % seed_max_value)
            current_seed=str(seed)
            
        newid=int(''.join([sft(current_time,'%S'),current_seed]))
        # save current time
        old_time=current_time
        # return a new id
        yield newid


def __uniquelongid__():
    mynow=datetime.now
    sft=datetime.strftime
    # store old datetime each time in order to check if we generate during same microsecond (glucky wallet !)
    # or if daylight savings event occurs (when clocks are adjusted backward) [rarely detected at this level]
    old_time=mynow() # fake init - on very speed machine it could increase your seed to seed + 1... but we have our contingency :)
    # manage seed
    seed_range_bits=14 # max range for seed
    seed_max_value=2**seed_range_bits - 1 # seed could not exceed 2**nbbits - 1
    # get random seed
    seed=random.getrandbits(seed_range_bits)
    current_seed=str(seed)
    # producing new ids
    while True:
        # get current time 
        current_time=mynow()
        if current_time <= old_time:
            # previous id generated in the same microsecond or Daylight saving time event occurs (when clocks are adjusted backward)
            seed = max(1,(seed + 1) % seed_max_value)
            current_seed=str(seed)
            
        newid=int(''.join([sft(current_time,'%f%S%M%H%d%m%Y'),current_seed]))
        # generate new id (concatenate seed and timestamp as numbers)
        #newid=hex(int(''.join([sft(current_time,'%f%S%M%H%d%m%Y'),current_seed])))[2:-1]
        #newid=int(''.join([sft(current_time,'%f%S%M%H%d%m%Y'),current_seed]))
        #newid=int(''.join([sft(current_time,'%S%f%d%m%Y'),current_seed]))
        #newid=int(''.join([sft(current_time,'%S%f%d%m'),current_seed]))
        # save current time
        old_time=current_time
        # return a new id
        yield newid

""" you get a new id for each call of uniqueid() """
uniqueid=__uniqueid__().__next__
uniquelongid=__uniquelongid__().__next__
uniqueshortid= __uniqueshortid__().__next__
if __name__ == '__main__':
    
    #m=[uniqueid() for _ in range(10)]
    
    print(uniqueid())
    print(uniqueid())
    print(uniqueid())
    print(uniqueid())
    print(uniqueid())
    
#import unittest
#class UniqueIdTest(unittest.TestCase):
#    def testGen(self):
#        for _ in range(3):
#            m=[uniqueid() for _ in range(10)]
#            self.assertEqual(len(m),len(set(m)),"duplicates found !")





