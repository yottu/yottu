'''
Created on Oct 4, 2015

'''
import subprocess

# FIXME: Setting to turn on/off
# FIXME: Handle Exception if notify-send from libnotify-bin (debian) isn't installed
# FIXME: Handle Exception if notify-send can't reach the notification daemon (such as dunst)

class Notifier(object):
	@staticmethod
	def send(name, message):
		try:
			subprocess.Popen(['notify-send', name, message])
		except OSError:
			raise
		return