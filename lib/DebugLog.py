import time

'''
Created on Sep 28, 2015

'''

class DebugLog(object):

	
	def __init__(self, wl='000', outputFile="debug.log", debugLevel=3):
		self.debugLevel = debugLevel
		self.outputFile = outputFile
		self.wl = wl
		
	def compad(self, message):
		if self.wl != '000':
			try:
				timePrefix = time.strftime("%H:%M ")
				self.wl.compadout(timePrefix + message)
			except:
				pass		
		
		
	def msg(self, message, logLevel=1, e=""):
		if logLevel <= self.debugLevel:
			self.compad(message)
			if e:
				message = str(time.ctime()) + " " + str(message) + " (E: " + str(type(e).__name__) + ": " + str(e) + ")"
			else:
				message = str(time.ctime()) + " " + str(message) 
						
			try:
				with open(self.outputFile, 'a') as fh:
					fh.write(message + "\n")
			except:
				raise
			
	def warn(self, e, logLevel=1, msg=""):
		self.msg("Warning (Level " + str(logLevel) + "): " + str(type(e).__name__) + ": " + str(e) + " " + msg, logLevel)		
			
	def excpt(self, e, logLevel=1, msg="", cn=""):
		if cn:
			cn += ": "
		self.msg("Exception (Level " + str(logLevel) + "): " + cn + str(type(e).__name__) + ": " + str(e) + " " + msg, logLevel)
