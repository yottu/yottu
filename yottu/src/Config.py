'''
Created on Oct 21, 2015

'''

import ConfigParser
import DebugLog
import os
from os.path import expanduser
from ConfigParser import NoSectionError, DuplicateSectionError


class Config(object):
	def __init__(self, configDir, configFile):
		self.homeDir = expanduser("~/")
		self.configDir = configDir
		self.configFile = configFile
		self.configFullPath = self.homeDir + self.configDir + self.configFile
		self.log = DebugLog.DebugLog()
		self.cfg = ConfigParser.ConfigParser()
	
	
	def set(self, key, value):
		try:
			self.cfg.set('Main', key, value)
		except DuplicateSectionError as w:
			self.log.warn(w)
			pass
		
	def readConfig(self):
		try:
			self.cfg.read(self.configFullPath)
		except Exception as e:
			self.log.excpt(e)
			
			
	def writeConfig(self):

		try:
			if not os.path.exists(self.homeDir + self.configDir):
				os.makedirs(self.homeDir + self.configDir)
				
			with open(self.configFullPath, 'w') as fh:
				self.cfg.write(fh)
		
		except Exception as e:
			self.log.excpt(e)
			
	def getSettings(self):
		self.readConfig()
		try:
			items = self.cfg.items('Main')
		except NoSectionError:
			self.cfg.add_section("Main")
			items = []
		return items