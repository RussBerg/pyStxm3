#!/usr/bin/python

import threading
import time
import numpy as np
import h5py

from sm.stxm_control.stxm_utils.nexus.nxstxm import update_data_whileopen, get_data_whileopen

exitFlag = 0




        
class myWriterThread (threading.Thread):
    def __init__(self, threadID, name, fname, w_fname, entry, num_writes=400, sim_closefile=False):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.entry = entry
        self.w_fname = w_fname
        self.num_writes = num_writes
        self.name = name
        self.fname = fname
        f = h5py.File(fname,  "r")
        self.nf = h5py.File(w_fname,  "w")
        #self.nf.create_group(self.entry)
        f.copy(self.entry, self.nf)
        self.nf.swmr_mode = True
        self.sim_lose_file = sim_closefile

    def run(self):
        print("Starting " + self.name)
        for i in range(self.num_writes):
            arr = np.random.rand(250,250)
            arr[0][0] = i
            update_data_whileopen(self.nf,self.entry, arr)
            # your code
        if(not self.sim_lose_file):    
            self.nf.close()
        else:
            print('leaving writer without closing file')    
        print("Exiting " + self.name)
        #threadLock.release()



class myReaderThread (threading.Thread):
    def __init__(self, threadID, name, fname, entry, num_reads=200):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.fname = fname
        self.entry = entry
        self.num_reads = num_reads
        self.nf = h5py.File(fname,  "r", swmr=True)
        
    def run(self):
        print("Starting " + self.name)
        for i in range(self.num_reads):
            #self.nf.id.refresh()
            data = get_data_whileopen(self.nf,self.entry)
            s = self.name
            if(data is not None):
                print(s + '] Read data[0][0][0:3]: ', data[0][0][0:3])
            else:
                print('%s] data not ready' % self.name)    
            # your code
        self.nf.close()
        print("Exiting " + self.name)

fname = r'C:/controls/py2.7/Beamlines/sm/data/guest/testdir/testswmr.hdf5'
w_fname = r'C:/controls/py2.7/Beamlines/sm/data/guest/testdir/testswmr_w.hdf5'


#threadLock = threading.Lock()
threads = []
num_writes=500
num_reads=300
# Create new threads
thread1 = myWriterThread(1, "myWriterThread-1", fname, w_fname, 'entry1458838195411', num_writes=num_writes, sim_closefile=False)
thread2 = myReaderThread(2, "myReaderThread-2", w_fname, 'entry1458838195411', num_reads=num_reads)
thread3 = myReaderThread(2, "myReaderThread-3", w_fname, 'entry1458838195411', num_reads=num_reads)
thread4 = myReaderThread(2, "myReaderThread-4", w_fname, 'entry1458838195411', num_reads=num_reads)

start_time = time.clock()
# Start new Threads

thread2.start()
thread3.start()
thread1.start()
thread4.start()
# Add threads to thread list
threads.append(thread1)
threads.append(thread2)
threads.append(thread3)
threads.append(thread4)

# Wait for all threads to complete
for t in threads:
    t.join()

print("Exiting Main Thread")
elapsed_time = time.clock() - start_time
print('thread test: Elapsed time for updating the data with %d writes and %d reads is %.4f seconds' % (num_writes, num_reads, elapsed_time))
