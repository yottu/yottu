#!/usr/bin/python
import curses
import locale

from lib.DebugLog import DebugLog
from lib.CommandInterpreter import CommandInterpreter
from lib.WindowLogic import WindowLogic
from lib.Updater import Updater
import sys
from time import sleep

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
		dlog = DebugLog(wl)
		dlog.msg("Logging started")

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


