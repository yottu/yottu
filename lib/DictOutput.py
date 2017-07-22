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
import json
from Config import Config
from DebugLog import DebugLog
from bs4 import BeautifulSoup

import warnings
import unicodedata
import time
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
		
		self.subfile = None
		self.subfile_start = None
		self.append_to_subfile = False # Write new comment to subfile
		
		self.title = u"yottu v0.3 - https://github.com/yottu/yottu - Init: <DictOutput>".encode('utf-8')
		self.cfg = Config()

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
		

		
	def refresh(self, jsonobj):
		self.thread = jsonobj
		
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
	
	
			refposts = ""
			try: country = posts['country']
			except: country = ""
			try:
				com = posts['com']
				com = re.sub('<br>', ' ', com)
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
						
					self.bp.threadFetcher.update_n = 3
					self.comment_tbm_timeout -= 1
				
			except:
				pass
			
	
			try:
				
				# TODO maybe just use the structure from 4chan's json. Maybe.
				self.tdict[no] = {'country':country, 'name':name, 'time':time,
						'com':com, 'trip':trip, 'color':color, 'filename':filename,
						'tim':tim, 'ext':ext, 'marked':marked, 'refposts':refposts }
				
				def filter_scan(filterdict):
					filter_matched = False
					for rule in json.loads(filterdict):

						for section in json.loads(rule['filter']):
							try: test = json.loads(rule['filter'])
							except: pass
							debug.msg("--" + str(self.tdict[no][section]) + " in " + str(test[section]))
							if self.tdict[no][section] in test[section]:
								debug.msg("--Matched")
								filter_matched = True
							if self.tdict[no][section] not in test[section]:
								debug.msg("--Not matched")
								filter_matched = False
								break
							
					debug.msg("--Matched: " + str(filter_matched))
					return filter_matched
				
				# Scan for matched filters 
				filter_matched = False
				if self.cfg.get('filter.ignore.list') and filter_scan(self.cfg.get('filter.ignore.list')):
					filter_matched = True
				if self.cfg.get('filter.except.list') and filter_scan(self.cfg.get('filter.except.list')):
					filter_matched = False
				
						
				# ####### FIXME: Remove. This is to test filtering
# 				pattern = re.compile(ur'Japanese', re.UNICODE)
# 				filter_matched = False
# 				if country in ["DE", "TH"] and self.bp.board == "int" and name == "Anonymous" \
# 					and trip == "" and pattern.search(self.originalpost['com']):
# 					
# 					filter_matched = True
# 					
# 					# Exception for filter
# 					for letter in com:
# 						if unicodedata.east_asian_width(letter) in ['W', 'F']:
# 							filter_matched = False
# 							break
# 				elif country == "US" and name == "Anonymous":
# 					filter_matched = True
							
				if filter_matched:
					debug.msg("--FILTER TEST: Skipping comment: " + str(no))
					continue
			except Exception as err:
				debug.warn(err, msg=">>>in DictOutput.refresh() (-> filter)")
				
			try:			
				#if filter_matched:	
				#		
				#	continue
				####### End of filter test ###########
				

				
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
				self.title = "yottu v0.3 - https://github.com/yottu/yottu - <BoardPad>"
				debug.msg("Couldn't set title" + str(e) + "\n")
				pass
		
		
		self.subfile_append(com)
			

		
	
	def subfile_append(self, com):
		''' Output comment to subfile when streaming a video '''
		if self.append_to_subfile:
			
			with open(self.subfile, 'a',) as fh:
				
				xpos = str((100+20)%480)
				fh.write("Dialogue: 0," + self.subfile_time(time.time()) +".00," + self.subfile_time(int(time.time())+10) + ".00,testStyle,,")
				fh.write('0000,0000,0000,,{\\move(1440,'
						+ xpos + ',-512,' + xpos + ')}{\\fad(1000,1000)}')
				fh.write(com.encode('utf-8')) # TODO FIXME Security
				fh.write("\n") 
		
	
	def subfile_time(self, thetime):
		''' return time formatted for subtitle file (HH:MM:SS) '''
		seconds_since_start = int(thetime) - int(self.subfile_start)
		sec_format = str("%02i" % ((seconds_since_start)%60))
		min_format = str("%02i" % ((seconds_since_start/60)%60))
		hour_format = str("%02i" % ((seconds_since_start/60/60)%99))
		time_formatted = hour_format + ":" + min_format + ":" + sec_format
		return time_formatted
	
	def getTitle(self):
		return self.title
	
	# TODO this might need its own class
	def create_sub(self, postno, subfile):
		''' create a subfile for overlaying comments over webm '''
		self.subfile = subfile
		self.subfile_start = time.time()
		try:
			comments = []
			for post in self.tdict:
				for refpost in self.tdict[post]['refposts']:
					if str(refpost) == str(postno):
						if not self.tdict[post]['com'] == "[File only]":
							comments.append(re.sub('(\d+)', '', self.tdict[post]['com']))
						continue
					continue
			
			if comments:
				with open(subfile, 'w') as fh:
					fh.write(u"[Script Info]\n# Thank you Liisachan from forum.doom9.org\n".encode('utf-8'))
					fh.write("ScriptType: v4.00+\nCollisions: Reverse\nPlayResX: 1280\n")
					fh.write("PlayResY: 1024\nTimer: 100.0000\n\n")
					fh.write("[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, ")
					fh.write("SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, ")
					fh.write("StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, ")
					fh.write("Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
					fh.write("Style: testStyle,Verdana,48,&H40ffffff,&H00000000,&Hc0000000")
					fh.write(",&H00000000,-1,0,0,0,100,100,0,0.00,1,1,0,8,0,0,0,0\n")
					fh.write("[Events]\nFormat: Layer, Start, End, Style, Actor, MarginL, ")
					fh.write("MarginR, MarginV, Effect, Text\n")
					for i, com in enumerate(comments):
						xpos = str((i*100+20)%480)
						time_start = str("%02i" % (i+1)) # FIXME math
						time_end = str("%02i" % (i+12)) # FIXME math
						fh.write("Dialogue: 0,0:00:" + time_start +".00,0:00:" + time_end + ".00,testStyle,,")
						fh.write('0000,0000,0000,,{\\move(1440,'
								+ xpos + ',-512,' + xpos + ')}{\\fad(1000,1000)}')
						fh.write(com.encode('utf-8')) # TODO FIXME Security
						fh.write("\n") 
			else:
				return False
		except Exception:
			raise
		
		return True
				
		
		
		
	
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
	
