'''
Created on Oct 4, 2015

'''
import subprocess

class Notifier(object):
	@staticmethod
	def send(message):
		subprocess.Popen(['notify-send', message])
		return