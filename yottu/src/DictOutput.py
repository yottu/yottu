# -*- coding: utf-8 -*-
'''
Created on Oct 4, 2015

'''
from __future__ import division
import curses
from random import randint
import re
import math
from Notifier import Notifier
import datetime
from DebugLog import DebugLog

class DictOutput(object):
	def __init__(self, bp):
		self.bp = bp
		self.tdict = {}
		self.thread = ""
		self.nickname = "asdfasd"
		self.title = u"yottu v0.1 - https://github.com/yottu/yottu - Init: <DictOutput>".encode('utf-8')
		
	def refresh(self, json):
		self.thread = json
		
		try:
			debug = DebugLog("debug.log")
		except:
			raise
		
		
		for posts in self.thread['posts']:
			try:
			# skip if record found in dictionary
				no = posts['no']
				
				# Post is OP
				try:
					if posts['resto'] is 0:
						self.tdict['OP'] = {'no': posts['no'], 'sub': posts['sub'].encode('utf-8'), 'semantic_url': posts['semantic_url'].encode('utf-8')}					
				
				except Exception as e:
					debug.msg("Exception:" + e.msg() + "\n")
					raise
					
				if no in self.tdict:
					continue
				
				name = posts['name']
				time = datetime.datetime.fromtimestamp(posts['time']).strftime('%H:%M')
			except:
				continue
					
			curses.use_default_colors()
			for i in range(0, curses.COLORS):  # @UndefinedVariable
				curses.init_pair(i + 1, i, -1)
						
			# assign color to post number
			color = randint(2, 255)
	
	
	
			try: country = posts['country']
			except: country = ""
			try:
				com = posts['com']
				com = re.sub('<br>', ' ', com)
				refposts = ""
				refposts = re.findall('&gt;&gt;(\d+)', com)
				com = re.sub('&gt;&gt;(\d+)', '\g<1> ', com)
				com = re.sub('&#039;', '\'', com)
				com = re.sub('&gt;', '>', com)
				com = re.sub('&lt;', '<', com)
				com = re.sub('&quot;', '"', com)
				com = re.sub('<[^<]+?>', '', com)
			except: com = "[File only]"
			try:
				trip = posts['trip']
			except:
				trip = ""
	
	
	
			self.tdict[no] = {'country':country, 'name':name, 'time':time, 'com':com, 'trip':trip, 'color':color}
	
#			try:
#				line = u' '.join((time, ">>" + str(no), country, "<" + name + ">", com)).encode('utf-8')
#			except:
#				raise
			
			
			# FIXME this entire block should be in its own class			
			try:
				self.bp.addstr("", curses.color_pair(color))
				self.bp.addstr(time)
				self.bp.addstr(" >>" + str(no), curses.color_pair(color))
				self.bp.addstr(" " + country)
	
				if re.match(self.nickname, name) is not None:
					self.bp.addstr(" <" + self.nickname + "> ", curses.A_BOLD)
	
				else:
					self.bp.addstr(" <" + name.encode('utf8') + "> ")
				#self.bp.addstr(com.encode('utf8'))
				
				comlist = com.split()
				try:
					for word in comlist:
						if word not in refposts:
							self.bp.addstr(u''.join((word + " ")).encode('utf8'))
						else:
							# Comment and reference color encoding
							try:
								refcolor = self.tdict[int(word)]['color']
								self.bp.addstr(">>" + word + " ", curses.color_pair(refcolor))
								# if reference points to nickname, higligt the name
								if re.match(self.tdict[int(word)]['name'], self.nickname):
									self.bp.addstr("(You) ", curses.A_BOLD | curses.color_pair(221))
									Notifier.send(com)
#								if re.match(word, threadno):
#									self.bp.addstr("(OP) ", curses.A_BOLD | curses.color_pair(197))
							except:
								self.bp.addstr(word)
				except:
					self.bp.addstr("[File only]")
			except:
				raise
	
			self.bp.addstr("\n")
			
		try:
			self.title = self.tdict['OP']['sub']
		except Exception as e:
			self.title = self.tdict['OP']['com']
			debug.msg("Couldn't set title" + str(e) + "\n")
			pass
		
		
		
	def get_tdict(self):
		return self.__tdict


	def set_tdict(self, value):
		self.__tdict = value

	
	def getTitle(self):
		return self.title

	
	
	tdict = property(get_tdict, set_tdict, None, None)
	
	
