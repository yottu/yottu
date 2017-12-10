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
from Database import Database
from bs4 import BeautifulSoup

import warnings
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
		
		self.dlog = DebugLog(self)
		
		self.subfile = None
		self.subfile_start = None
		self.subfile_lasttime = None # Time last sub got displayed
		self.append_to_subfile = False # Write new comment to subfile
		self.subfile_count = 0 # Number of comments in live subfile
		
		self.title = u"yottu v0.3 - https://github.com/yottu/yottu - Init: <DictOutput>".encode('utf-8')
		self.cfg = Config()
		
		self.db = Database()

	def get_tdict(self):
		return self.__tdict


	def set_tdict(self, value):
		self.__tdict = value
		
	def mark(self, comment):
		''' look for comment to be marked as user post in the next n refreshes '''
		self.comment_tbm_timeout = 3 # is decreased every refresh
		self.comment_tbm = comment # FIXME does not work with utf-8
		self.comment_tbm = re.sub('>>(\d+)', '\g<1>', self.comment_tbm)
		self.comment_tbm = re.sub('\n', ' ', self.comment_tbm)
		

	def refresh(self, jsonobj):
		self.thread = jsonobj
		
		#self.tdict['OP'] = {'no': 213, 'com': 'unset', 'sub': 'unset'.encode('utf-8'), 'semantic-url': 'unset'.encode('utf-8')}
		
		# Get some information about the thread (post count, reply count, etc) from the first post 
		try:
			self.originalpost.update({'no': self.thread['posts'][0]['no']})
			
			try: 
				self.originalpost.update({'replies': self.thread['posts'][0]['replies']})
				self.originalpost.update({'images': self.thread['posts'][0]['images']})
				self.originalpost.update({'unique_ips': self.thread['posts'][0]['unique_ips']})
				thread_stats = " " + str(self.originalpost['replies']) + "R " \
					+ str(self.originalpost['images']) + "I " \
					+ str(self.originalpost['unique_ips']) + "P"
				self.bp.tb.stats = thread_stats
			except Exception as e: 
				self.dlog.warn(e, logLevel=3, msg=">>>in DictOutput.refresh()")
			
			try:
				self.originalpost.update({'semantic_url': self.thread['posts'][0]['semantic_url'].encode('utf-8')})
			except:
				pass 
			
			try:
				com = self.clean_html(self.thread['posts'][0]['com']) 
				self.originalpost.update({'com': com.encode('utf-8')})
				self.title = self.originalpost['com']
			except: pass
			
			try:
				sub = self.clean_html(self.thread['posts'][0]['sub'])
				self.originalpost.update({'sub': sub.encode('utf-8')})
				self.title = self.originalpost['sub']
			except:
				pass
			
		except Exception as e:
			self.dlog.warn(e, msg=">>>in CatalogOutput.refresh()", cn=self.__class__.__name__)
			raise
		
		db_posts = []
		try:
			# Array containing posts from previous sessions
			db_posts = self.db.get_postno_from_threadno(self.originalpost['no'])
		except:
			self.dlog.excpt(e, msg=">>>in refresh() -> db_posts", cn=self.__class__.__name__)
		
		for posts in self.thread['posts']:
			
			# skip post if base data can't be processed
			try:
				
				no = posts['no']
				
				# skip post if it was already processed
				if no in self.tdict:
					continue
				
				name = posts['name']
				time = datetime.datetime.fromtimestamp(posts['time']).strftime('%H:%M')
			except:
				continue
				
			# assign color to post number
			curses.use_default_colors()  # @UndefinedVariable
			for i in range(0, curses.COLORS):  # @UndefinedVariable
				curses.init_pair(i + 1, i, -1)  # @UndefinedVariable
			color = randint(3, 255)
	
	
			refposts = "" # posts referenced in a reply
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
				fsize = posts['fsize']
			except:
				fsize = 0
				
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
					
					self.dlog.msg("com: " + str(com) + " tbm: " + str(self.comment_tbm))
					# TODO regex match with n percentage accuracy should work better
					if com == self.comment_tbm:
						marked = True
						self.comment_tbm = None
						self.comment_tbm_timeout = 0
						self.bp.update_db(no)
						
					self.bp.threadFetcher.update_n = 3
					self.comment_tbm_timeout -= 1
				if no in db_posts:
					marked = True
			except:
				pass
			
	
			try:
				
				# TODO maybe just use the structure from 4chan's json. Maybe.
				self.tdict[no] = {'country':country, 'name':name, 'time':time,
						'com':com, 'trip':trip, 'color':color, 'filename':filename,
						'tim':tim, 'ext':ext, 'marked':marked, 'refposts':refposts,
						'fsize':fsize }
				
				def filter_scan(filterdict):
					filter_matched = False
					for rule in json.loads(filterdict):

						for section in json.loads(rule['filter']):
							
							
							try: test = json.loads(rule['filter'])
							except: pass
							
							if self.tdict[no][section] in test[section] and self.tdict[no][section]:
								self.dlog.msg("--Matched: " + str(self.tdict[no][section]) + " in " + str(test[section]), 4)
								filter_matched = True
							elif self.tdict[no][section] not in test[section]:
								self.dlog.msg("--Not matched: " + str(self.tdict[no][section]) + " in " + str(test[section]), 4)
								filter_matched = False
								break
							else:
								self.dlog.msg("--Not matched (section does not exist): " + str(section), 4)
								filter_matched = False
								break
							
					self.dlog.msg("--Matched (" + str(rule) + "): " + str(filter_matched), 4)
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
					self.dlog.msg("--FILTER TEST: Skipping comment: " + str(no))
					continue
			except Exception as err:
				self.dlog.warn(err, msg=">>>in DictOutput.refresh() (-> filter)")
				
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
									except Exception as e:
											self.dlog.excpt(e, msg=">>>in DictOutput.refresh()", cn=self.__class__.__name__)
											raise
									
								# highlight OP reference
								if re.match(word, str(self.originalpost['no'])):
									try:
										self.bp.addstr("(OP) ", curses.A_BOLD | curses.color_pair(197), indent)  # @UndefinedVariable
									except:
										raise
										pass

							except Exception as e:
								#self.dlog.msg("DictOutput: " + str(e))
								self.bp.addstr(word + " ", curses.A_DIM, indent)  # @UndefinedVariable
								pass
								
				except:
					self.bp.addstr("[File only]", curses.A_DIM, indent)  # @UndefinedVariable
			except:
				raise
	
			self.bp.addstr("\n", curses.A_NORMAL, indent)  # @UndefinedVariable
			
		
		self.subfile_append(com)
		
		# refetch entire thread on post count mismatch
		try:
			if len(self.tdict) != int(self.thread['posts'][0]['replies']) + 1:
				self.bp.update_thread(notail=True)
		except Exception as e:
			self.dlog.excpt(e, msg=">>>in DictOutput.refresh() ->refetch", cn=self.__class__.__name__)

		
	def subfile_append(self, com):
		''' Output comment to subfile when streaming a video '''
		if self.append_to_subfile:
			
			with open(self.subfile, 'a',) as fh:
				# FIXME replace hardcoded 5 with subtitle display duration
				xpos = str((self.subfile_count*100+20)%480)
				
				# ceil of comment length divided by 50 # FIXME hard coded 50
				for i in range(0, -(-len(com))//50+1):
					fh.write("Dialogue: 0," + self.subfile_time(time.time()+3*i) +".00," + self.subfile_time(int(time.time())+3*(i+1)) + ".00,testStyle,,")
					fh.write('0000,0000,0000,,{\\move(1440,'
							+ xpos + ',-512,' + xpos + ')}{\\fad(1000,1000)}')
					fh.write(com.encode('utf-8')[i*50:(i+1)*50]) # TODO FIXME Security
					fh.write("\n")
					
				self.subfile_count += 1 
		
	
	def subfile_time(self, thetime):
		''' return time formatted for subtitle file (HH:MM:SS) '''
		
		# seconds since last subtitle was displayed
		self.subfile_lasttime = int(thetime) - int(self.subfile_start)
		
		sec_format = str("%02i" % ((self.subfile_lasttime)%60))
		min_format = str("%02i" % ((self.subfile_lasttime/60)%60))
		hour_format = str("%02i" % ((self.subfile_lasttime/60/60)%99))
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
		except Exception as e:
			self.dlog.excpt(e, msg=">>>in DictOutput.create_sub()", cn=self.__class__.__name__)
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
	
