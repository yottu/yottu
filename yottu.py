#!/usr/bin/python

# __   __   _   _
# \ \ / /__| |_| |_ _  _
#  \ V / _ \  _|  _| || |
#   |_|\___/\__|\__|\_,_|
# https://github.com/yottu/yottu
# License: GPLv3 (see LICENSE)
#  or https://www.gnu.org/licenses/gpl-3.0.en.html

import sys
import curses
import locale

sys.path.insert(0, 'lib')

from WindowLogic import WindowLogic
from CommandInterpreter import CommandInterpreter
from Updater import Updater


locale.setlocale(locale.LC_ALL, '')





def main(argv):
	def __call__(self):
		pass

	stdscr = curses.initscr()
	curses.noecho()  # @UndefinedVariable
	curses.cbreak()  # @UndefinedVariable
	stdscr.keypad(1)
	curses.start_color()

	
	try:	
		wl = WindowLogic(stdscr)
		#wl.start()
	except Exception as e:
		raise
		
	try:
		dlog = wl.dlog
		dlog.msg("Logging debug output to " + str(dlog.outputFile))
		dlog.msg("Images will be cached in " + wl.cfg.get('file.image.directory'))

		ci = CommandInterpreter(stdscr, wl)
		ci.start()
		
		updater = Updater(stdscr, wl)
		updater.start()
	except Exception as e:
		dlog.excpt(e)
		raise

	ci.join()
	dlog.msg("Command Interpreter joined.")
	updater.stop()
	updater.join()
	dlog.msg("Updater joined.")
	#wl.stop()
	#wl.join()
	dlog.msg("Thread Fetcher joined.")

	curses.nocbreak()  # @UndefinedVariable
	stdscr.keypad(0)
	curses.echo()  # @UndefinedVariable
	curses.endwin()  # @UndefinedVariable
	curses.resetty()  # @UndefinedVariable
	dlog.msg("Terminal restored.")


sys.stdout.write("\x1b]2;%s\x07" % "Yottu (._. )")
curses.wrapper(main)


