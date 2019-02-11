# coding=utf-8
import threading
import time
import logging

try:
	import cygnuslog  # pylint: disable=unused-import
except ImportError:
	pass

log = logging.getLogger('cygnus.pynatconnd')


class BaseThread(threading.Thread):
	def __init__(self, shared_statistics):
		threading.Thread.__init__(self)
		self.running = False
		self.alive_time = time.time()
		self.time_diff = 0
		self.shared_statistics = shared_statistics

	def alive(self):
		self.alive_time = time.time()

	def stop(self):
		self.running = False
