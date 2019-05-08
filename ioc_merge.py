from pcaspy import  Driver
from threading import Thread 
import logging
import numpy as np
import time
import ueye_ioc_2 as ueye_ioc
_logger = logging.getLogger("epicsUeye")





pvdb = {
	'AOI' : {
		'type': 'int',
		'unit': '-',
		'count': 4
		},

	'XSize' : {
		'type': 'int',
		'unit': '-'
		},

	'YSize' : {
		'type': 'int',
		'unit': '-'
		},
		

	'Exposure' : {
		'type': 'float',
		'unit': 'ms'
		},

	'ExposureMin' : {
		'type': 'float',
		'unit': 'ms'
		},

	'ExposureMax' : {
		'type': 'float',
		'unit': 'ms'
		},

	'PixelClock' : {
		'type': 'int',
		'unit': 'Mbit/s'
		},

	'PixelClockMin' : {
		'type': 'int',
		'unit': 'Mbits/s'
		},

	'PixelClockMax' : {
		'type': 'int',
		'unit': 'Mbits/s'
		},

	'SetBuffer' : {
		'type': 'int',
		'unit': '-'
		},

	'Acquire' : {
		'type': 'int',
		'unit': '-',
		},

	'AcquireBG': {
		'type': 'enum',
		'enums': ['Acquire','Remove'],
		'value': 0,
		},

	'AcquireBG_RB': {
		'type': 'enum',
		'enums': ['Set','NONE'],
		'value': 1,
		},
  	

	'Grabbing' : {
		'type': 'int',
		'unit': '-'
		},

	'Image' : {
		'type': 'int',
		'unit': '-',
		'count': 1311720,		
		},

	'ImageN': {
		'type': 'int',
		'asyn': True,
		'unit': '-',		
		},

	'Status': {
		'type': 'int',
		'unit': '-',
		'value': 1,	
		},
 }
 



def make_pvs(prefix):
	pvdb = {
	'%s:AOI'%prefix : {
		'type': 'int',
		'unit': '-',
		'count': 4
		},

	'%s:XSize'%prefix : {
		'type': 'int',
		'unit': '-'
		},

	'%s:YSize'%prefix : {
		'type': 'int',
		'unit': '-'
		},
		

	'%s:Exposure'%prefix : {
		'type': 'float',
		'unit': 'ms'
		},

	'%s:ExposureMin'%prefix : {
		'type': 'float',
		'unit': 'ms'
		},

	'%s:ExposureMax'%prefix : {
		'type': 'float',
		'unit': 'ms'
		},

	'%s:PixelClock'%prefix : {
		'type': 'int',
		'unit': 'Mbit/s'
		},

	'%s:PixelClockMin'%prefix : {
		'type': 'int',
		'unit': 'Mbits/s'
		},

	'%s:PixelClockMax'%prefix : {
		'type': 'int',
		'unit': 'Mbits/s'
		},

	'%s:SetBuffer'%prefix : {
		'type': 'int',
		'unit': '-'
		},

	'%s:Acquire'%prefix : {
		'type': 'int',
		'unit': '-'
		},

	'%s:AcquireBG'%prefix: {
		'type': 'enum',
		'enums': ['Acquire','Remove'],
		'value': 0,
		},

	'%s:AcquireBG_RB'%prefix: {
		'type': 'enum',
		'enums': ['Set','NONE'],
		'value': 1,
		},

	'%s:Grabbing'%prefix : {
		'type': 'int',
		'unit': '-'
		},

	'%s:Image'%prefix : {
		'type': 'int',
		'unit': '-',
		'count': 1311720,		
		},

	'%s:ImageN'%prefix: {
		'type': 'int',
		'asyn': True,
		'unit': '-',		
		},

	'%s:Status'%prefix: {
		'type': 'int',
		'value': 1,	
		},

	'%s:FWHM_X'%prefix: {
		'type': 'float',
		'value': 0.0,
		},

	'%s:FWHM_Y'%prefix: {
		'type': 'float',
		'value': 0.0,
		},

	'%s:Xm'%prefix: {
		'type': 'float',
		'value': 0.0,
		},

	'%s:Ym'%prefix: {
		'type': 'float',
		'value': 0.0,
		},

	'%s:STATS'%prefix: {
		'type': 'enum',
		'enums': ['Off', 'On'] ,
		'value': 0,
		},

	'%s:STATS_ARR'%prefix: {
		'type': 'float',
		'count': 4 
		},

 }
 
	return pvdb
	

 
class iocMerge(Driver):
	def __init__(self, cams):
		"""Get array of pair [cam, Prefixs] where prefix is xxxx:PREFIX:yyyy""" 
		Driver.__init__(self)
		self.n_iocs=0
		self.ioc=[]
		self.prefix=[]
		for i in cams:
			self.n_iocs+=1
			self.ioc.append(ueye_ioc.ThorCamIOC(i[0],self, i[1]))
			self.prefix.append(i[1])

	def read(self, reason):
		pre=reason.split(":")
		if pre[0] in self.prefix:
			inx=self.prefix.index(pre[0])
		else:
			return
		
		answ=self.ioc[inx].read(pre[1])
		self.updatePVs()

		return self.getParam(reason)
			
	def write(self, reason, value):
		pre=reason.split(":")
		if pre[0] in self.prefix:
			inx=self.prefix.index(pre[0])
		
		answ=self.ioc[inx].write(pre[1], value)
		self.updatePVs()

		
		
	
		
