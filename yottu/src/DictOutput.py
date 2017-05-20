# -*- coding: utf-8 -*-
'''
Created on Oct 4, 2015

'''
from __future__ import division
import curses
from random import randint
import re
from Notifier import Notifier
import datetime
from DebugLog import DebugLog
from bs4 import BeautifulSoup

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

class DictOutput(object):
	def __init__(self, bp):
		self.bp = bp
		self.tdict = {} # contains all posts (including OP)
		self.originalpost = {} # contains the OP post
		self.thread = ""
		self.nickname = "asdfasd"
		self.title = u"yottu v0.1 - https://github.com/yottu/yottu - Init: <DictOutput>".encode('utf-8')

	def get_tdict(self):
		return self.__tdict


	def set_tdict(self, value):
		self.__tdict = value

		
	def refresh(self, json):
		self.thread = json
		
		try:
			debug = DebugLog("debug.log")
		except:
			raise
		
		
		#self.tdict['OP'] = {'no': 213, 'com': 'unset', 'sub': 'unset'.encode('utf-8'), 'semantic-url': 'unset'.encode('utf-8')}
		
		for posts in self.thread['posts']:
			try:
				
				# skip if record found in dictionary
				no = posts['no']
				
				
				# Post is OP
				try:
					if posts['resto'] == 0:
						try: 
							self.originalpost.update({'no': no})
						except: 
							self.originalpost.update({'no': 1234567890})
							pass
						
						try: self.originalpost.update({'semantic_url': posts['semantic_url'].encode('utf-8')})
						except: pass 
						
						try:
							com = self.clean_html(posts['com']) 
							self.originalpost.update({'com': com.encode('utf-8')})
						except: pass
						
						try:
							sub = self.clean_html(posts['sub'])
							self.originalpost.update({'sub': sub.encode('utf-8')})
						except:
							pass
						
				
				except Exception as e:
					debug.msg("DictOutput: Error while processing OP: " + str(e))
					raise
					
				if no in self.tdict:
					continue
				
				name = posts['name']
				time = datetime.datetime.fromtimestamp(posts['time']).strftime('%H:%M')
			except:
				continue
					
			curses.use_default_colors()  # @UndefinedVariable
			for i in range(0, curses.COLORS):  # @UndefinedVariable
				curses.init_pair(i + 1, i, -1)  # @UndefinedVariable
						
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
				#com = re.sub('&#039;', '\'', com)
				#com = re.sub('&gt;', '>', com)
				#com = re.sub('&lt;', '<', com)
				#com = re.sub('&quot;', '"', com)
				#com = re.sub('<[^<]+?>', '', com)
				com = self.clean_html(com)
			except: com = "[File only]"
			try:
				trip = posts['trip']
			except:
				trip = ""
			try:
				filename = self.clean_html(posts['filename'])
			except:
				filename = ""
				
			try:
				tim = posts['tim']
			except:
				tim = ""
			try:
				ext = self.clean_html(posts['ext'])
			except:
				ext = ""
	
	
	
			self.tdict[no] = {'country':country, 'name':name, 'time':time,
							'com':com, 'trip':trip, 'color':color, 'filename':filename,
							'tim':tim, 'ext':ext }
	
#			try:
#				line = u' '.join((time, ">>" + str(no), country, "<" + name + ">", com)).encode('utf-8')
#			except:
#				raise
			
			
			# FIXME this entire block should be in its own class			
			try:
				
				# Write [TIME] <Name>
				self.bp.addstr("", curses.color_pair(color))  # @UndefinedVariable
				self.bp.addstr(time)
				
				self.bp.addstr(" >>" + str(no), curses.color_pair(color))  # @UndefinedVariable

					
				# Add country code	
				self.bp.addstr(" " + country)
	
				# Make own nickname bold
				if re.match(self.nickname, name) is not None:
					self.bp.addstr(" <" + self.nickname + "> ", curses.A_BOLD)  # @UndefinedVariable
	
				# Make name decoration bold if file is attached
				else:
					if filename:
						self.bp.addstr(" <", curses.A_BOLD)  # @UndefinedVariable
						self.bp.addstr(name.encode('utf8'))
						self.bp.addstr("> ", curses.A_BOLD)  # @UndefinedVariable
					else:
						self.bp.addstr(" <" + name.encode('utf8') + "> ")
				#self.bp.addstr(com.encode('utf8'))
				
				
				comlist = com.split()
				
				try:
					
# 					# Post filename if exists
# 					try:
# 						if filename:
# 							self.bp.addstr("[", curses.A_BOLD)  # @UndefinedVariable
# 							self.bp.addstr(filename[:12])
# 							self.bp.addstr("] ", curses.A_BOLD)  # @UndefinedVariable
# 					except:
# 						pass
					
					# Iterate over every word in a comment
					for word in comlist:
						
						# refposts contains all >>(\d+) in a comment
						if word not in refposts:
							# Output non-reference
							self.bp.addstr(u''.join((word + " ")).encode('utf8'))
							
						# Handle references (>>(\d+))	
						else:
							
							# Comment and reference color encoding
							try:
								refcolor = self.tdict[int(word)]['color']
								self.bp.addstr(">>" + word + " ", curses.color_pair(refcolor))  # @UndefinedVariable
								
								# Add (You) to referenced posts written by self.nickname
								if re.match(self.tdict[int(word)]['name'], self.nickname):
									self.bp.addstr("(You) ", curses.A_BOLD | curses.color_pair(221))  # @UndefinedVariable
									try:
										Notifier.send(name, com)
									except:
										pass
									
								# highlight OP reference
								if re.match(word, str(self.originalpost['no'])):
									try:
										self.bp.addstr("(OP) ", curses.A_BOLD | curses.color_pair(197))  # @UndefinedVariable
									except:
										pass

							except Exception as e:
								debug.msg("DictOutput: " + str(e))
								self.bp.addstr(word)
								pass
								
				except:
					self.bp.addstr("[File only]")
			except:
				raise
	
			self.bp.addstr("\n")
			
		try:
			self.title = self.originalpost['sub']
		except:
			try: 
				self.title = self.originalpost['com']
			except Exception as e:
				self.title = "yottu v0.1 - https://github.com/yottu/yottu - <BoardPad>"
				debug.msg("Couldn't set title" + str(e) + "\n")
				pass
		
		
	
	def getTitle(self):
		return self.title
	
	# source: https://stackoverflow.com/questions/328356/extracting-text-from-html-file-using-python
	def clean_html(self, html):
		soup = BeautifulSoup(html)
		
		# kill all script and style elements
		for script in soup(["script", "style"]):
			script.extract()
		
		# get text
		text = soup.get_text()
		
		# break into lines and remove leading and trailing space on each
		lines = (line.strip() for line in text.splitlines())
		
		# break multi-headlines into a line each
		chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
		
		# drop blank lines
		text = '\n'.join(chunk for chunk in chunks if chunk)
		
		return(text)
	
	
	tdict = property(get_tdict, set_tdict, None, None)
	
