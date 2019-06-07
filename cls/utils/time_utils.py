'''
Created on Apr 24, 2015

@author: bergr
'''
import datetime
from time import mktime, strftime, strptime, gmtime

def msec_to_sec(ms):
	return(ms*0.001)

class CST(datetime.tzinfo):
		def utcoffset(self, dt):
			return(datetime.timedelta(hours=-6))
		def dst(self, dt):
			return(datetime.timedelta(0))
		def tzname(self,dt):
			return("Saskatchewan Canada")

def make_timestamp_now():
	"""
	create a ISO 8601 formatted time string for the current time and return it
	"""
	t = datetime.datetime.now(tz=CST()).isoformat()
	return(t)



def secondsToStr(sec):
	return (strftime("%H:%M:%S", gmtime(sec)))

def datetime_string_to_seconds(s):
	'''
	'END_TIME': '2017-09-22T09:07:02.833000-06:00',
	'START_TIME': '2017-09-22T09:06:23.628000-06:00',

	:param s:
	:return:
	'''
	from datetime import datetime
	import time
	s2 = s.split('.')[0]
	d = datetime.strptime(s2, "%Y-%m-%dT%H:%M:%S")
	sec = time.mktime(d.timetuple())
	return(sec)
