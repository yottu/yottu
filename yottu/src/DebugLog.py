import time

'''
Created on Sep 28, 2015

'''
from email import message

class DebugLog(object):

	
	def __init__(self, wl='000', outputFile="debug.log", debugLevel=3):
		self.debugLevel = debugLevel
		self.outputFile = outputFile
		self.wl = wl
		
	def compad(self, message):
		if self.wl != '000':
			try:
				timePrefix = time.strftime("[%H:%M] ")
				self.wl.compadout(timePrefix + message)
			except:
				pass		
		
		
	def msg(self, message, logLevel=1):
		if logLevel <= self.debugLevel:
			self.compad(message)
			message = str(time.clock()) + " " + message 
						
			try:
				with open(self.outputFile, 'a') as fh:
					fh.write(message + "\n")
			except:
				raise
			
	def warn(self, e, logLevel=1):
		self.msg("Warning (" + str(logLevel) + "): " + str(type(e).__name__) + ": " + str(e), logLevel)		
			
	def excpt(self, e, logLevel=1):
		self.msg("Exception (" + str(logLevel) + "): " + str(type(e).__name__) + ": " + str(e), logLevel)