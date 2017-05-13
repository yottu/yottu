#!/usr/bin/python
import curses
import locale

from DebugLog import DebugLog
from CommandInterpreter import CommandInterpreter
from WindowLogic import WindowLogic

locale.setlocale(locale.LC_ALL, '')

def main(argv):
	def __call__(self):
		pass


	
	stdscr = curses.initscr()
	curses.noecho()
	curses.cbreak()
	stdscr.keypad(1)
	curses.start_color()
	
	try:
		wl = WindowLogic(stdscr)
		wl.start()
	except Exception as e:
		raise
		
	try:
		dlog = DebugLog(wl)
		dlog.msg("Logging started")

		ci = CommandInterpreter(stdscr, wl)
		ci.start()
	except Exception as e:
		dlog.excpt(e)
		raise

	ci.join()
	dlog.msg("Command Interpreter joined.")
	wl.stop()
	wl.join()
	dlog.msg("Thread Fetcher joined.")

	curses.nocbreak()
	stdscr.keypad(0)
	curses.echo()
	curses.endwin()
	curses.resetty()
	dlog.msg("Terminal restored.")

curses.wrapper(main)


