#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading
import logging
import datetime
import copy

try:
	import cygnuslog  # pylint: disable=unused-import
except ImportError:
	pass

from . import base_thread

log = logging.getLogger('cygnus.netfilter')


class GarbageCollectorThread(base_thread.BaseThread):  # pylint: disable=too-many-instance-attributes
	def __init__(self, shared_resources):
		base_thread.BaseThread.__init__(self, shared_resources['statistics'])
		log.debug("Initialzing the Garbage Collector thread", level=4)
		self.setName('GarbageCollector')
		self.timer_set = False
		self.shared_data = shared_resources['data']
		self.configuration = shared_resources['conf']
		assert shared_resources['lock'] is not None
		self.shared_data_lock = shared_resources['lock']
		self.ev = threading.Event()

	def run(self):
		log.debug("Garbage cleaner thread running", level=4)
		self.running = True
		while self.running:
			self.ev.wait(self.configuration['data']['garbage_cleaner_interval'])

			log.debug("Starting garbage collector")
			before_cleaning = len(self.shared_data)
			share_data_copy = copy.deepcopy(self.shared_data)
			with self.shared_data_lock:
				for key, value in share_data_copy.items():
					data_time = datetime.datetime.strptime(value['time'], '%Y-%m-%d %H:%M:%S')
					time_now = datetime.datetime.now()
					time_diff = time_now - data_time
					if time_diff.seconds > self.configuration['data']['life_span']:
						if key in self.shared_data:
							del self.shared_data[key]
							self.shared_statistics['expired_data'] += 1
							log.debug("Removed the entry %s from the shared dictionary ", key, level=4)
						else:
							log.debug("Couldn't find the entry %s in the shared dictionary ", key)
					else:
						log.debug("timestamp of %s not exceeded the life span", key, level=10)

			self.timer_set = False
			log.debug("garbage collector finished - dict size is %s - deleted %s items", len(self.shared_data), before_cleaning - len(self.shared_data))

			self.ev.clear()

		log.debug("Stopped Garbage Collector thread", level=1)

	def stop(self):
		log.debug("Stopping Garbage Collector thread", level=4)
		self.running = False
		self.ev.set()
