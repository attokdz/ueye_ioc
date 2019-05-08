from pyueye import ueye
import logging
import numpy as np
from threading import Thread 

_logger = logging.getLogger("epicsUeye")

def dummy():
	pass

class ueyeCam:
	def __init__(self, serial):
		nc=ueye.c_int()
		self.status=True
		self._bgImage=0
		self.bg=0
		if ueye.is_GetNumberOfCameras(nc):
			_logger.error("Error Wrong number of cameras")			
			return 
		lst=ueye.UEYE_CAMERA_LIST((ueye.UEYE_CAMERA_INFO*nc.value))
		lst.dwCount=nc.value
		ueye.is_GetCameraList(lst)
		index=None
		for i in range(nc.value):
			_logger.info("Got the following ccd: %s"%lst.uci[i].SerNo)
			if (lst.uci[i].SerNo==serial):
				index=i
				break
		if index is None:
			_logger.error("SerNo %s not found."%serial)
			return 			
			
		if lst.uci[index].dwStatus:
			_logger.error("Camera %d is already busy."%index)

		self.hcam=ueye.HIDS(index)
		if ueye.is_InitCamera(self.hcam, None):
			_logger.error("Error inializating camera.")
			self.status=True
			return
		self.bufCount=0
		self.bitsPixel=8
		self.Imgs=None
		self.LastSeqBuf1=ueye.c_mem_p(1)
		self.acq=False
		self.grabbingCB=dummy
		self.grabbing=False
		self.setColorMode(ueye.IS_CM_MONO8)
		if self.LoadSettings():
			_logger.error("error laoding camera settings")
			sys.exit()
		self.status=False

	def LoadSettings(self):
		if self.getSensorInfo():
			_logger.error("Error retriving sensor information.")
			return True
		if self.getColorMode():
			_logger.error("Error getting color mode.")
			return True
		if self.getAOI():
			_logger.error("Error getting color mode.")
			return True
		if self.getPixelClock():
			_logger.error("Error getting color mode.")
			return True
		if self.getExposureRange():
			_logger.error("Error getting color mode.")
			return True
		if self.getExposureTime():
			_logger.error("Error getting color mode.")
			return True
		if self.getPixelClockRange():
			_logger.error("Error getting color mode.")
			return True
		return False

	def getSensorInfo(self):
		self.sensorInfo=ueye.SENSORINFO()
		if ueye.is_GetSensorInfo(self.hcam, self.sensorInfo):
			self.status=True
			_logger.error("Error retriving sensor information.")
			return True
		return False

	def getColorMode(self):
		self.colormode=ueye.is_SetColorMode(self.hcam, ueye.IS_GET_COLOR_MODE)
		self.bitsPixel=self.bitspixel(self.colormode)

	def setColorMode(self, mode):
		if ueye.is_SetColorMode(self.hcam, mode):
			self.status=True
			return True
		return False

	def getAOI(self):
		self.AOI=ueye.IS_RECT()
		if ueye.is_AOI(self.hcam, ueye.IS_AOI_IMAGE_GET_AOI, self.AOI, ueye.sizeof(self.AOI)):
			_logger.error("Error retrinving AOI")
			self.status=True
			return True
		x0=self.AOI.s32X.value
		y0=self.AOI.s32Y.value
		width=self.AOI.s32Width.value
		height=self.AOI.s32Height.value
		self.xaxis=np.arange(width)+x0
		self.yaxis=np.arange(height)+y0
		return False

	def setAOI(self, x0, y0, width, height):
		self.AOI=ueye.IS_RECT()
		if (x0<0)|((x0+width)>self.sensorInfo.nMaxWidth.value):
			self.status=True
			return True
		if (y0<0)|((y0+height)>self.sensorInfo.nMaxHeight.value):
			self.status=True
			return True
			
		self.AOI.s32X.value=x0
		self.AOI.s32Y.value=y0
		self.AOI.s32Width.value=width
		self.AOI.s32Height.value=height
		self.xaxis=np.arange(width)+x0
		self.yaxis=np.arange(height)+y0
		if ueye.is_AOI(self.hcam, ueye.IS_AOI_IMAGE_SET_AOI, self.AOI, ueye.sizeof(self.AOI)):
			self.status=True
			return True
		return False

	def getPixelClock(self):
		self.pixelClock=ueye.c_uint()
		if ueye.is_PixelClock(self.hcam, ueye.IS_PIXELCLOCK_CMD_GET, self.pixelClock, ueye.sizeof(ueye.c_uint)):
			self.status=True
			_logger.error("Error retrinving PixelClock")
			return True
		return False

	def getPixelClockRange(self):
		self.PixelClockRange=[ueye.c_uint() for i in range(3)]
		self.PixelClockRange=(ueye.c_uint*3)(*self.PixelClockRange)
		if ueye.is_PixelClock(self.hcam, ueye.IS_PIXELCLOCK_CMD_GET_RANGE, self.PixelClockRange, ueye.sizeof(self.PixelClockRange)):
			_logger.error("Error retrinving pixelclock range")
			self.status=True
			return True
		

	def setPixelClock(self, value):
		self.getPixelClockRange()
		if (value<self.PixelClockRange[0].value) & (value>self.PixelClockRange[1].value):
			self.status=True
			return True

		ran=np.arange(self.PixelClockRange[0].value, self.PixelClockRange[1].value, self.PixelClockRange[2].value)
		nwv=ueye.c_uint(ran[np.abs(ran-value).argmin()])
		if ueye.is_PixelClock(self.hcam, ueye.IS_PIXELCLOCK_CMD_SET, nwv, ueye.sizeof(nwv)):
			self.status=True
			return True
		return False

	
	def getExposureTime(self):
		self.exposureTime=ueye.c_double()
		if ueye.is_Exposure(self.hcam, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE, self.exposureTime, ueye.sizeof(ueye.c_double)):
			self.status=True
			_logger.error("Error retrinving Exposure time")
			return True
		return False

	def getExposureRange(self):
		ExposureRange=[ueye.c_double() for i in range(3)]
		self.ExposureRange=(ueye.c_double*3)(*ExposureRange)
		if ueye.is_Exposure(self.hcam, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE, self.ExposureRange, ueye.sizeof(self.ExposureRange)):
			_logger.error("Error retrinving exposure range")
			self.status=True
			return True


	def setExposureTime(self, value):
		self.getExposureRange()
		if (value<self.ExposureRange[0].value) & (value>self.ExposureRange[1].value):
			self.status=True
			return True

		ran=np.arange(self.ExposureRange[0].value, self.ExposureRange[1].value, self.ExposureRange[2].value)
		nwv=ueye.c_double(ran[np.abs(ran-value).argmin()])
		if ueye.is_Exposure(self.hcam, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE, nwv, ueye.sizeof(nwv)):
			self.status=True
			return True
		return False

	def unLockLastBuffer(self):
		rv= ueye.is_UnlockSeqBuf(self.hcam, ueye.IS_IGNORE_PARAMETER, self.LastSeqBuf)

	def LockLastBuffer(self):
		rv= ueye.is_LockSeqBuf(self.hcam, ueye.IS_IGNORE_PARAMETER, self.LastSeqBuf)

	def setBuffer(self, size):
		self.bufCount=size
		if self.Imgs is not None:
			for i in range(self.bufCount):
				rv=ueye.is_FreeImageMem (self.hcam, self.Imgs[i], self.bufIds[i])
				if rv:
					self.status=True
					return True				
				self.bufIds[i] = 0
		if self.getAOI():
			self.status=True
			return True
		self.imgWidth=self.AOI.s32Width.value
		self.imgHeight=self.AOI.s32Height.value
		self.Imgs=[ueye.c_mem_p() for i in range(size)]
		self.bufIds=[ueye.c_int() for i in range(size)]


		for i in range(self.bufCount):
			rv=ueye.is_AllocImageMem(self.hcam, self.imgWidth, self.imgHeight,self.bitsPixel, self.Imgs[i], self.bufIds[i])
			if rv:
				self.status=True
				return True
			rv=ueye.is_AddToSequence (self.hcam, self.Imgs[i], self.bufIds[i])
			if rv:
				self.status=True
				return True
		self.LineInc=ueye.c_int()
		rv=ueye.is_GetImageMemPitch (self.hcam, self.LineInc)
		if rv:
			self.status=True
			return True
		return False


	def bitspixel(self, colormode):
		if colormode==ueye.IS_CM_MONO8:
			return 8
		elif colormode==ueye.IS_CM_MONO12	or colormode==ueye.IS_CM_MONO16 or colormode==ueye.IS_CM_BGR565_PACKED  or colormode==ueye.IS_CM_UYVY_PACKED   or colormode==ueye.IS_CM_CBYCRY_PACKED:
			return 16
		elif colormode==ueye.IS_CM_RGB8_PACKED or colormode==ueye.IS_CM_BGR8_PACKED:
			return 24
		elif colormode==ueye.IS_CM_RGBA8_PACKED or colormode==ueye.IS_CM_BGRA8_PACKED or colormode==ueye.IS_CM_RGBY8_PACKED or colormode==ueye.IS_CM_BGRY8_PACKED:
			return 32
		else: 
			return 8

	def  GetNextBuffer(self):
		""" Get the next valid image buffer"""
		self.NewSeqBuf1=ueye.c_mem_p()
		tries=0
		while True:
			rv= ueye.is_GetImageMem(self.hcam, self.NewSeqBuf1)
			if self.NewSeqBuf1.value != self.LastSeqBuf1.value: 
				break
			tries+=1
			if tries ==3: 
				return True
    
			rv=ueye.is_EnableEvent(self.hcam, ueye.IS_SET_EVENT_FRAME)		
			rv= ueye.is_WaitEvent(self.hcam, ueye.IS_SET_EVENT_FRAME, 1000)	
			rv=ueye.is_DisableEvent(self.hcam, ueye.IS_SET_EVENT_FRAME)
       
		self.LastSeqBuf1.value=self.NewSeqBuf1.value	
		return False


	def GrabImage(self):
		if self.GetNextBuffer():
			return True
		self.LastImage=ueye.get_data(self.LastSeqBuf1, self.imgWidth, self.imgHeight, self.bitsPixel, self.LineInc, True)
		return False

	def ContinousGrabbing(self):
		while self.grabbing:
			if self.GetNextBuffer():
				return True
			self.LastImage=ueye.get_data(self.LastSeqBuf1, self.imgWidth, self.imgHeight, self.bitsPixel, self.LineInc, True).astype(np.int16)
			if self.bg:
				self.LastImage-=self._bgImage
				self.LastImage=self.LastImage.clip(min=0)
			self.grabbingCB()
	
	def StartContGrabbing(self):
		if not self.acq:
			self.startAcq()
		self.grabbingThread=Thread()
		self.grabbingThread.run=self.ContinousGrabbing
		self.grabbing=True
		self.grabbingThread.start()

	def startAcq(self):
		if ueye.is_CaptureVideo(self.hcam, ueye.IS_DONT_WAIT):
			return True
		self.acq=True
		return False

	def stopAcq(self):
		if ueye.is_StopLiveVideo(self.hcam, ueye.IS_DONT_WAIT):
			return True
		self.acq=False
		return False


		
		
			
		
			
		
		
		
		
		
			

			

		

			



		

		
				
		
		
				


		
