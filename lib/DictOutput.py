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
		self.thread = "" # json
		self.nickname = self.bp.get_nickname()
		self.comment_tbm = None
		self.comment_tbm_timeout = 0
		self.title = u"yottu v0.2 - https://github.com/yottu/yottu - Init: <DictOutput>".encode('utf-8')

	def get_tdict(self):
		return self.__tdict


	def set_tdict(self, value):
		self.__tdict = value
		
	def mark(self, comment):
		''' look for comment to be marked as user post in the next n refreshes '''
		self.comment_tbm_timeout = 3 # is decreased every refresh
		self.comment_tbm = comment
		self.comment_tbm = re.sub('>>(\d+)', '\g<1>', self.comment_tbm)
		self.comment_tbm = re.sub('\n', ' ', self.comment_tbm)
		

		
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
			color = randint(3, 255)
	
	
	
			try: country = posts['country']
			except: country = ""
			try:
				com = posts['com']
				com = re.sub('<br>', ' ', com)
				refposts = ""
				# save all post quotes in a list (without >>)
				refposts = re.findall('&gt;&gt;(\d+)', com)
				# remove >> from quotes for now
				com = re.sub('&gt;&gt;(\d+)', '\g<1>', com)
				#com = re.sub('&#039;', '\'', com)
				#com = re.sub('&gt;', '>', com)
				#com = re.sub('&lt;', '<', com)
				#com = re.sub('&quot;', '"', com)
				#com = re.sub('<[^<]+?>', '', com)
				com = self.clean_html(com)
			except: com = "[File only]"  # @UndefinedVariable
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
				file_ext_short = ext[1:2].upper()
			except:
				ext = ""
				file_ext_short = " "
				
			# Compare comment content to recently posted comment
			try:
				marked = False
				if self.comment_tbm_timeout > 0:
					
					debug.msg("com: " + str(com) + " tbm: " + str(self.comment_tbm))
					# TODO regex match with n percentage accuracy should work better
					if com == self.comment_tbm:
						marked = True
						self.comment_tbm = None
						self.comment_tbm_timeout = 0
						
					self.comment_tbm_timeout -= 1
				
			except:
				pass
	
	
			# TODO maybe just use the structure from 4chan's json. Maybe.
			self.tdict[no] = {'country':country, 'name':name, 'time':time,
							'com':com, 'trip':trip, 'color':color, 'filename':filename,
							'tim':tim, 'ext':ext, 'marked':marked }
	
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
				
				# Count of characters that are in every new BoardPad line (for indentation on nl in bp)
				indent = len(time)+len(str(no))+len(country)+4
	
				# Make own nickname bold
				if re.match(str(self.nickname), name) or marked:
					
# 					if not self.nickname:
# 						nick = "Anonymous"
# 					else:
# 						nick = self.nickname
					self.bp.addstr(" <" + file_ext_short + name + "> ", curses.A_BOLD)  # @UndefinedVariable
	
				# Make name decoration stand out if file is attached
				else:
					self.bp.addstr(" <", curses.color_pair(240))  # @UndefinedVariable
					self.bp.addstr(file_ext_short, curses.color_pair(240) | curses.A_BOLD)  # @UndefinedVariable
					self.bp.addstr(name.encode('utf8'), curses.A_DIM)  # @UndefinedVariable
					self.bp.addstr("> ", curses.color_pair(240))  # @UndefinedVariable
				
				# width of name including unicode east asian characters + len("<  > ") == 5	
				indent += self.bp.calcline(name.encode('utf8'))+5
				
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
							self.bp.addstr(u''.join((word + " ")).encode('utf8'), curses.A_NORMAL, indent)  # @UndefinedVariable
						# Handle references (>>(\d+))	
						else:
							
							# Comment and reference color encoding
							try:
								refcolor = self.tdict[int(word)]['color']
								self.bp.addstr(">>" + word + " ", curses.color_pair(refcolor), indent)  # @UndefinedVariable
								
								# Add (You) to referenced posts written by self.nickname
								if re.match(self.tdict[int(word)]['name'], str(self.nickname)) or self.tdict[int(word)]['marked'] == True:
									self.bp.addstr("(You) ", curses.A_BOLD | curses.color_pair(221), indent, mentioned=True)  # @UndefinedVariable
									try:
										Notifier.send(name, com)
									except:
										raise
										pass
									
								# highlight OP reference
								if re.match(word, str(self.originalpost['no'])):
									try:
										self.bp.addstr("(OP) ", curses.A_BOLD | curses.color_pair(197), indent)  # @UndefinedVariable
									except:
										raise
										pass

							except Exception as e:
								#debug.msg("DictOutput: " + str(e))
								self.bp.addstr(word + " ", curses.A_DIM, indent)  # @UndefinedVariable
								pass
								
				except:
					self.bp.addstr("[File only]", curses.A_DIM, indent)  # @UndefinedVariable
			except:
				raise
	
			self.bp.addstr("\n", curses.A_NORMAL, indent)  # @UndefinedVariable
			
		try:
			self.title = self.originalpost['sub']
		except:
			try: 
				self.title = self.originalpost['com']
			except Exception as e:
				self.title = "yottu v0.2 - https://github.com/yottu/yottu - <BoardPad>"
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
	
