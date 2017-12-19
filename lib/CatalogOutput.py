# -*- coding: utf-8 -*-
'''
Created on Oct 4, 2015

'''
from __future__ import division
import curses
from random import randint
import re
import datetime

class CatalogOutput(object):
	def __init__(self, cp, search=""):
		self.cp = cp
		self.dlog = cp.dlog
		self.search = search
		self.tdict = {}
		self.result_postno = [] # list of OPs containing search term
		self.initial_run = True
		
		
	def refresh(self, json):
		self.catalog = json
		
		self.cp.stdscr.noutrefresh()
		for pages in self.catalog:
			
			page = str(pages['page'])
			
			for threads in pages['threads']:
				
				try:
					no = threads['no']

					# skip if record found in dictionary	
					if no in self.tdict:
						continue
					
					name = threads['name']
					time = datetime.datetime.fromtimestamp(threads['time']).strftime('%H:%M')
				except:
					continue
									
				# assign color to post number # start at unreserved colors
				color = randint(11, 240)
	
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
					
					if self.search:					
						if (not re.search(str.lower(self.search), sub.lower())) and (not re.search(str.lower(self.search), com.lower())):
							continue
						self.result_postno.append(no)
					
					self.cp.addstr("", curses.color_pair(color)) # @UndefinedVariable
					self.cp.addstr(time)
					self.cp.addstr(" >>" + str(no), curses.color_pair(color)) # @UndefinedVariable
					self.cp.addstr(" R:" + str(replies), curses.A_BOLD) # @UndefinedVariable
					self.cp.addstr(" " + country)
		
	
					self.cp.addstr(" <" + name.encode('utf8') + "> ", curses.A_DIM)  # @UndefinedVariable
					
					sublist = sub.split()
					comlist = com.split()
					try:
						for word in sublist:
							self.cp.addstr(u''.join((word + " ")).encode('utf8'), curses.A_BOLD)  # @UndefinedVariable
						
						if sub:
							self.cp.addstr("- ")
						
						for word in comlist:
							self.cp.addstr(u''.join((word + " ")).encode('utf8'))
					except:
						self.cp.addstr("[File only]")
				except Exception as e:
					self.dlog.excpt(e, ">>>in CatalogOutput.refresh()", cn=self.__class__.__name__)
					raise

				self.cp.addstr("\n")
			
			if self.initial_run: 
				self.cp.addstr("\n---- Page: " + page + "\n\n")

		self.initial_run = False
		
		curses.doupdate()  # @UndefinedVariable

		return self.result_postno	
		
	def get_tdict(self):
		return self.__tdict


	def set_tdict(self, value):
		self.__tdict = value

	
	def getTitle(self):
		return self.title

	
	
	tdict = property(get_tdict, set_tdict, None, None)
	
	
