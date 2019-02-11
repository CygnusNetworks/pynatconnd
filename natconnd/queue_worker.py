#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
try:
	import cygnuslog  # pylint: disable=unused-import
except ImportError:
	pass

from . import base_thread
from . import nfct_cffi  # pylint: disable=no-name-in-module
from . import nfct_logger  # pylint: disable=no-name-in-module

log = logging.getLogger('cygnus.pynatconnd')


class QueueWorker(base_thread.BaseThread):
	def __init__(self, event_queue, shared_statistics):
		base_thread.BaseThread.__init__(self, shared_statistics)
		log.debug("Initializing  worker thread", level=4)
		self.setName('QueueWorker')
		self.event_queue = event_queue

	def run(self):
		log.debug("Starting worker thread", level=4)
		self.running = True
		log.debug("Creating an instance of NFCT logger", level=4)
		logger = nfct_cffi.NFCT()
		src = logger.generator()
		for x, ev_xml in enumerate(src):
			if x == 0:
				continue
			try:
				event = nfct_logger.parse_event(ev_xml)
			except Exception as e:
				log.error("Caught an exception %s", e)
				raise

			if not event:  # Commonly occurring error
				continue

			log.debug("Adding element %s to the queue", event, level=10)
			self.event_queue.put(event)
			self.shared_statistics['queue_size'] = self.event_queue.qsize()
			if not self.running:
				log.debug("Stoping the Receiver thread is running value is %s", self.running, level=1)
				break

	def stop(self):
		log.debug("stop method of Worker thread is called", level=1)
		self.running = False
