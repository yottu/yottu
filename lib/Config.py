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
	
	def __init__(self, configDir=".config/yottu/", configFile="config", debug=True):
		
		self.homeDir = expanduser("~/")
		self.configDir = configDir # i.e. .config/yottu/
		self.configDirFullPath = self.homeDir + self.configDir
		self.configFile = configFile # i.e. config
		self.configFullPath = self.homeDir + self.configDir + self.configFile # i.e. /home/user/.config/yottu/config
		
		self.debug = debug # avoid recursion loop if called by Config
		if debug:
			self.dlog = DebugLog.DebugLog()
		self.cfg = ConfigParser.SafeConfigParser()
		
		self.readConfig()

	def set_config_dir_full_path(self, value):
		self.__configDirFullPath = value


	def get_config_dir_full_path(self):
		return self.__configDirFullPath
	
	def defaults(self):
		''' returns dict with default settings '''
		return {
			'autojoin_threads' : '',
			'board.default': 'g', #    
			'config.autoload': 'False', # Load settings after /save
			'config.autosave': 'False', # Save settings after /set
			'proxy.socks.address': '127.0.0.1', # 
			'proxy.socks.enable': 'False', # 
			'proxy.socks.port': '9050', #   
			'user.options': '', #  
			'user.name': '', #
			'user.tripcode' : '', # 
			'file.image.autodownload': 'False', # 
			'file.image.directory': './cache/', # 
			'file.thumb.autodownload': 'False', # 
			'file.thumb.directory': './cache/thumbs/', #
			'file.video.autodownload': 'False', #  
			'file.video.directory': './cache/', # 
			'file.video.subfile': 'subfile.ass', #
			'filter.except.list': '', # "[ {'filter': {'country': ['DE']}, 'pattern':[]}, {'filter': {'country': ['JP']}, 'pattern':[] } ]", #
			'filter.ignore.list': '', # "[{'filter': {'name': 'Anonymous', 'country': ['DE', 'FR']}, 'pattern':['Japanese', 'OP']}]", #     
			'log.file.location': './debug.log', # 
			'log.level': '3' # 
		
			}

	def is_valid_key(self, key):
		
		if key in self.defaults():
			return True
		
		return False
	
	def set(self, key, value):
		''' sets key to json.dumps(value)'''
		try:
			if self.is_valid_key(key):
			# self.cfg is a ConfigParser object
				if value:
					self.cfg.set('Main', key, json.dumps(value))
				else:
					self.cfg.set('Main', key, json.dumps(None))

			else:
				raise KeyError('Invalid setting: ' + str(key))
		except KeyError as e:
			raise
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
		''' 
		get value(s) of key (returns bool, int or string, not json encoded)
		'''
		try:
			if not self.is_valid_key(key):
				raise KeyError('Invalid Key in config: ' + str(key))
			items = self.getSettings()
			#self.dlog.msg("listing " + str(json.dumps(dict(items)[key])))
			value = dict(items)[key]
			
			try:
				if str(value).lower() in ['false', 'no', 'nope', '0' ]:
					return False
				if str(value).lower() in ['true', 'yes', 'yup', '1' ]:
					return True
				if str(value) == 'None':
					return None
			except: pass
			
			try: return int(value)
			except: pass
			
			return value
		except:
			raise

		
	def readConfig(self):
		''' read settings from file and to self.cfg (ConfigParser object) '''
		try:
			self.cfg.read(self.configFullPath)

		except Exception as e:
			if self.debug:
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
		'''
		returns a list of all settings
		values are stored as json objects on disk 
		
		'''
		try:
			
			settings = {}
			
			# Get default settings
			settings.update(self.defaults())
			
			# Overwrite with setting from config file
			
			for key in self.cfg._sections[section]:
				try:
					if self.is_valid_key(key):
						
						settings.update({key: json.loads(self.cfg._sections[section][key])})
				except (ValueError, TypeError) as err:
					self.dlog.warn(err, msg=">>>in Config.getSettings() while parsing key: " + str(key))
					settings.update({key: self.cfg._sections[section][key]})
					continue
			items = settings.items()
			
		
		# Add section if it does not exist (currently only using 'Main')	
		except NoSectionError:
			self.cfg.add_section(section)
			items = []
		except Exception as err:
			self.dlog.excpt(err, msg=">>>in getSettings()", cn=self.__class__.__name__)
		return sorted(items)
	
# 	def get(self, key, section='Main'):
# 		'''returns values of key in section'''
# 		try:
# 			items = self.getSettings(section)
# 			return dict(items)[json.loads(key)]
# 		except:
# 			raise
		
		
	
	configDirFullPath = property(get_config_dir_full_path, set_config_dir_full_path, None, None)
