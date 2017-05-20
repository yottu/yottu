# -*- coding: utf-8 -*-
'''
Created on Oct 4, 2015

'''
from __future__ import division
import curses
from random import randint
import re
import datetime
from DebugLog import DebugLog

class CatalogOutput(object):
	def __init__(self, cp, search=""):
		self.cp = cp
		self.search = search
		self.tdict = {}
		
	def refresh(self, json):
		self.catalog = json
		
		try:
			debug = DebugLog("debug.log")
		except:
			raise
		
		
		for pages in self.catalog:
			for threads in pages['threads']:

				try:
					no = threads['no']

				# Post is OP
# 				try:
# 					if threads['resto'] is 0:
# 						self.tdict['OP'] = {'no': threads['no'], 'sub': threads['sub'].encode('utf-8'), 'semantic_url': threads['semantic_url'].encode('utf-8')}					
# 				
# 				except Exception as e:
# 					debug.msg("Exception:" + e.msg() + "\n")
# 					raise
# 				

					# skip if record found in dictionary	
					if no in self.tdict:
						continue
					
					name = threads['name']
					time = datetime.datetime.fromtimestamp(threads['time']).strftime('%H:%M')
				except:
					continue
					
				curses.use_default_colors() # @UndefinedVariable
				for i in range(0, curses.COLORS):  # @UndefinedVariable
					curses.init_pair(i + 1, i, -1) # @UndefinedVariable
						
				# assign color to post number
				color = randint(2, 255)
	
				try: replies = threads['replies']
				except: replies = ""
	
				try: sub = threads['sub']
				except: sub = ""
					
				try: country = threads['country']
				except: country = ""
				
				try:
					com = threads['com']
					com = re.sub('<br>', ' ', com)
# 				refposts = ""
# 				refposts = re.findall('&gt;&gt;(\d+)', com)
					com = re.sub('&gt;&gt;(\d+)', '\g<1> ', com)
					com = re.sub('&#039;', '\'', com)
					com = re.sub('&gt;', '>', com)
					com = re.sub('&lt;', '<', com)
					com = re.sub('&quot;', '"', com)
					com = re.sub('<[^<]+?>', '', com)
				except: com = "[File only]"
				try:
					trip = threads['trip']
				except:
					trip = ""
					
				self.tdict[no] = {'country':country, 'name':name, 'time':time,
								  'com':com, 'trip':trip, 'color':color, 'sub':sub, 'replies':replies}

			
				# Output tdict to pad
				try:
					
										
					if (not re.search(str.lower(self.search), sub.lower())) and (not re.search(str.lower(self.search), com.lower())):
						continue
					
					self.cp.addstr("", curses.color_pair(color)) # @UndefinedVariable
					self.cp.addstr(time)
					self.cp.addstr(" >>" + str(no), curses.color_pair(color)) # @UndefinedVariable
					self.cp.addstr(" R:" + str(replies), curses.A_BOLD) # @UndefinedVariable
					self.cp.addstr(" " + country)
		
	
					self.cp.addstr(" <" + name.encode('utf8') + "> ", curses.A_DIM)
					
					sublist = sub.split()
					comlist = com.split()
					try:
						for word in sublist:
							self.cp.addstr(u''.join((word + " ")).encode('utf8'), curses.A_BOLD)
						
						if sub:
							self.cp.addstr("- ")
						
						for word in comlist:
							self.cp.addstr(u''.join((word + " ")).encode('utf8'))
					except:
						self.cp.addstr("[File only]")
				except:
					raise
		
				self.cp.addstr("\n\n")
			
		
	def get_tdict(self):
		return self.__tdict


	def set_tdict(self, value):
		self.__tdict = value

	
	def getTitle(self):
		return self.title

	
	
	tdict = property(get_tdict, set_tdict, None, None)
	
	
