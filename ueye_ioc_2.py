from pcaspy import  Driver
from threading import Thread 
import logging
import numpy as np
import time
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
		'unit': '-'
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
 }
 

 
class ThorCamIOC():
	def __init__(self, camera, parent, prefix):
		self.cam=camera
		self.parent=parent
		self.prefix=prefix

		#self.cam.getPixelClockRange()
		self.setParam("PixelClockMin", self.cam.PixelClockRange[0])
		self.setParam("PixelClockMax", self.cam.PixelClockRange[1])
		self.stats=0
		
		#self.getExposureRange()
		self.read("AOI")
		self.read("PixelClock")
		self.read("Exposure")
		self.cam.grabbingCB=self.updateImage
		self.setParam("ImageN",0)
		self.nimages=0			
		self.updatePVs()

	def getExposureRange(self):
		self.cam.getExposureRange()
		self.setParam("ExposureMin", self.cam.ExposureRange[0].value)
		self.setParam("ExposureMax", self.cam.ExposureRange[1].value)
		self.parent.updatePVs()

		
	def read(self, reason):
		if reason=="AOI":
			if self.cam.getAOI():
				_logger.exception("Error retriving AOI")
				return 
			val=[self.cam.AOI.s32X.value, self.cam.AOI.s32Y.value, self.cam.AOI.s32Width.value, self.cam.AOI.s32Height.value]
			self.setParam(reason, val)
			self.updatePVs()

		elif reason=="XSize":
			self.setParam(reason, self.getParam("AOI")[2])

		elif reason=="YSize":
			self.setParam(reason,self.getParam("AOI")[3])

		elif reason=="ExposureMin":
			self.setParam("ExposureMin",self.cam.ExposureRange[0].value)

		elif reason=="ExposureMax":
			self.setParam("ExposureMax",self.cam.ExposureRange[1].value)		


		elif reason=="PixelClock":
			if self.cam.getPixelClock():
				_logger.exception("Error retriving PixelClock")
				return
			val=self.cam.pixelClock.value 
			self.setParam(reason, val)

		elif reason=="SetBuffer":
			val=self.cam.bufCount
			self.setParam(reason, not(val))

		elif reason=="Exposure":
			if self.cam.getExposureTime():
				_logger.exception("Error retriving Exposure time")
			val=self.cam.exposureTime.value
			self.setParam(reason, val)

		elif reason=="Acquire":
			self.setParam(reason, self.cam.acq)

		elif reason=="Grabbing":
			self.setParam(reason, self.cam.grabbing)		
			

		elif reason=="ImageN":
			self.setParam(reason, self.nimages)




			
	def write(self, reason, value):

		if reason=="PixelClock":
			if self.cam.setPixelClock(value):
				_logger.exception("Error setting PixelClock")
				return 		
			self.read(reason)
			self.cam.getPixelClockRange()
			self.read("Exposure")

		elif reason=="SetBuffer":
			if self.cam.setBuffer(value):
				_logger.exception("Error setting Buffer")
				return 
			self.read(reason)
			

		elif reason=="Exposure":
			if self.cam.setExposureTime(value):
				_logger.exception("Error setting PixelClock")
				return 	
			self.read(reason)

		elif reason=="AOI":
			if self.cam.setAOI(value[0], value[1], value[2], value[3]):
				_logger.exception("Error setting PixelClock")
				return 	
			self.read(reason)
			self.read("XSize")
			self.read("YSize")

		elif reason=="Acquire":
			if value:
				if self.cam.startAcq():
					_logger.exception("Error starting Acquisition")
					return
				
			else:
				if self.cam.stopAcq():
					_logger.exception("Error stoping Acquisition")
					return
			self.read(reason)

		elif reason=="Grabbing":
			if value:
				if self.cam.StartContGrabbing():
					_logger.exception("Error starting grabbing")
					return
			else:
				self.cam.grabbing=False
			self.read(reason)

		elif reason=="Image":
			self.setParam("Image", value)
			
		
		elif reason=="ImageN":
			self.nimages=value
			self.read(reason)

		elif reason=="AcquireBG":
			if value:
				self.cam.bg=False
				self.cam._bgImage=np.zeros(self.cam.LastImage.shape).astype(np.int16)
				self.setParam("AcquireBG_RB",1)
				print(self.cam._bgImage.mean())
			else:
				self.cam.bg=True
				self.cam._bgImage=self.cam.LastImage
				self.setParam("AcquireBG_RB",0)
			self.setParam(reason, value)

		elif reason=="STATS":
			self.stats=value
			self.setParam(reason, value)
		


	def updateImage(self):
 		self.setParam("Image", self.cam.LastImage)
		self.nimages+=1
		self.setParam("ImageN",self.nimages)
		if self.stats:
			self.make_stats()
		self.updatePV("Image")
		self.updatePV("ImageN")
		self.callbackPV('ImageN')
		
		#self.callbackPV('Image')

	def callbackPV(self, reason):
		self.parent.callbackPV("%s:%s"%(self.prefix, reason))

	def setParam(self, reason, value):
		self.parent.setParam("%s:%s"%(self.prefix, reason), value)

	def getParam(self, reason):
		return self.parent.getParam("%s:%s"%(self.prefix, reason))
	
	def updatePVs(self):
		self.parent.updatePVs()

	def updatePV(self, reason):
		self.parent.updatePV("%s:%s"%(self.prefix,reason))	

	def make_stats(self):
		im=self.cam.LastImage.reshape(self.cam.imgWidth, self.cam.imgHeight)
		px=im.sum(axis=1)
		py=im.sum(axis=0)
		norm=px.sum()
		x=(self.cam.xaxis*px).sum()/norm
		y=(self.cam.yaxis*py).sum()/norm
		fwhmx=np.abs((self.cam.xaxis-x)*px).sum()/norm
		fwhmy=np.abs((self.cam.yaxis-y)*py).sum()/norm
		self.setParam("STATS_ARR", [x,y,fwhmx,fwhmy])
		self.setParam("Xm", x)
		self.setParam("Ym", y)
		self.setParam("FWHM_X", fwhmx)
		self.setParam("FWHM_Y", fwhmy)
		self.updatePV("Xm")
		self.updatePV("Ym")
		self.updatePV("FWHM_X")
		self.updatePV("FWHM_Y")
		self.updatePV("STATS_ARR")
	


		
		
	
		
