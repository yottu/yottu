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
		self.configDir = configDir # i.e. .config/yottu/
		self.configDirFullPath = self.homeDir + self.configDir
		self.configFile = configFile # i.e. config
		self.configFullPath = self.homeDir + self.configDir + self.configFile # i.e. /home/user/.config/yottu/config
		
		self.log = DebugLog.DebugLog()
		self.cfg = ConfigParser.ConfigParser()

	def set_config_dir_full_path(self, value):
	    self.__configDirFullPath = value


	def get_config_dir_full_path(self):
		return self.__configDirFullPath

	
	
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
	
	configDirFullPath = property(get_config_dir_full_path, set_config_dir_full_path, None, None)
