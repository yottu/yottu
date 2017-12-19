import time
from Config import Config
from os.path import expanduser

'''
Created on Sep 28, 2015

'''

class DebugLog(object):

	
	def __init__(self, wl=None, outputFile="debug.log", debugLevel=3):
		
		self.wl = wl
		cfg = Config(debug=False)
		
		try: 
			self.outputFile = cfg.get('log.file.location') 
			self.outputFile = expanduser(self.outputFile)
		except:
			self.outputFile = outputFile
			
		try: self.debugLevel = cfg.get('log.level')
		except:	self.debugLevel = debugLevel
		
		
	def compad(self, message):
		if self.wl:
			try:
				timePrefix = time.strftime("%H:%M ")
				self.wl.compadout(timePrefix + message)
			except:
				pass		
		
		
	def msg(self, message, logLevel=1, e=""):
		if logLevel <= self.debugLevel:
			
			# Outputting level 5 leads to recursion loops
			if logLevel < 5:
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
			
	def warn(self, e, logLevel=1, msg="", cn=""):
		if cn:
			cn += ": "
		self.msg("Warning (Level " + str(logLevel) + "): " + cn + str(type(e).__name__) + ": " + str(e) + " " + msg, logLevel)		
			
	def excpt(self, e, logLevel=1, msg="", cn=""):
		if cn:
			cn += ": "
		self.msg("Exception (Level " + str(logLevel) + "): " + cn + str(type(e).__name__) + ": " + str(e) + " " + msg, logLevel)
