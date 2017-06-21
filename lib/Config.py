'''
Created on Oct 21, 2015

'''

import ConfigParser
import DebugLog
import os
import json
from os.path import expanduser
from ConfigParser import NoSectionError, DuplicateSectionError


class Config(object):
	'''
		(1) set key, val pairs with set(k,v) and get(k)
		(2) set key, json.dumps pairs with add(k,v) remove(k,v) and list(k)
	'''
	
	def __init__(self, configDir, configFile):
		
		self.homeDir = expanduser("~/")
		self.configDir = configDir # i.e. .config/yottu/
		self.configDirFullPath = self.homeDir + self.configDir
		self.configFile = configFile # i.e. config
		self.configFullPath = self.homeDir + self.configDir + self.configFile # i.e. /home/user/.config/yottu/config
		
		self.dlog = DebugLog.DebugLog()
		self.cfg = ConfigParser.SafeConfigParser()
		
		self.readConfig()

	def set_config_dir_full_path(self, value):
		self.__configDirFullPath = value


	def get_config_dir_full_path(self):
		return self.__configDirFullPath

	
	
	def set(self, key, value):
		''' sets key to json.dumps(value)'''
		try:
			# self.cfg is a ConfigParser object
			self.cfg.set('Main', key, json.dumps(value))
		except DuplicateSectionError as w:
			self.dlog.warn(w)
			pass
		except Exception as e:
			self.dlog.excpt(e)
			pass
		
	def add(self, key, key_sub, val_sub):
		'''add json.dumps to value'''
		
		new_keyval = {key_sub : val_sub}
		keyval = []
		
		# try to load existing values
		try:
			keyval = json.loads(self.get(key))
		except:
			pass
		
		keyval.append(new_keyval)
		
		json_keyval = json.dumps(json.JSONEncoder().encode(keyval))
		self.cfg.set('Main', key, json_keyval)
		
	# TODO: implement
	def remove(self, key, key_sub, val_sub):
		'''remove json.dumps from value'''
# 		try:
# 			keyval = json.loads(self.get(key))
# 		except:
# 			pass
# 		del keyval['key_sub']
		pass
	
	def clear(self, key):
		'''set to empty list'''
		# FIXME: is the encode really necessary 
		self.cfg.set('Main', key, json.dumps(json.JSONEncoder().encode([])))
	
	def get(self, key):
		'''get value(s) of key (returns key of json.loads(dict)'''
		try:
			items = self.getSettings()
			#self.dlog.msg("listing " + str(json.dumps(dict(items)[key])))
			value = dict(items)[key]
			if value:
				return json.loads(value)
		except KeyError or ValueError:
			pass
		except:
			raise

		
	def readConfig(self):
		''' read settings from file and to self.cfg (ConfigParser object) '''
		try:
			self.cfg.read(self.configFullPath)
		except Exception as e:
			self.dlog.excpt(e)
			
			
	def writeConfig(self):

		try:
			if not os.path.exists(self.homeDir + self.configDir):
				os.makedirs(self.homeDir + self.configDir)
				
			with open(self.configFullPath, 'wb') as fh:
				self.cfg.write(fh)
		
		except Exception as e:
			self.dlog.excpt(e)
			
# 	def getSetting(self, key, section='Main'):
# 		''' returns value of key in section '''
# 		items = self.getSettings(section)
# 		return dict(items)[key]
			
	def getSettings(self, section='Main'):
		'''returns a list of all settings'''
		try:
			items = self.cfg.items(section)
		except NoSectionError:
			self.cfg.add_section(section)
			items = []
		return items
	
# 	def get(self, key, section='Main'):
# 		'''returns values of key in section'''
# 		try:
# 			items = self.getSettings(section)
# 			return dict(items)[json.loads(key)]
# 		except:
# 			raise
		
		
	
	configDirFullPath = property(get_config_dir_full_path, set_config_dir_full_path, None, None)
