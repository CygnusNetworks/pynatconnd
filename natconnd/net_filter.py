#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading
import logging

try:
	import cygnuslog  # pylint: disable=unused-import
except ImportError:
	pass

from . import base_thread

log = logging.getLogger('cygnus.pynatconnd')


class NetFilter(base_thread.BaseThread):  # pylint: disable= too-many-instance-attributes
	def __init__(self, event_queue, shared_resource):
		base_thread.BaseThread.__init__(self, shared_resource['statistics'])
		log.debug("Initializing Netfilter thread", level=2)
		self.setName('NetFilter')
		self.event_queue = event_queue
		self.shared_data = shared_resource['data']
		self.configuration = shared_resource['conf']
		assert shared_resource['lock'] is not None
		self.shared_data_lock = shared_resource['lock']

		self.timer_list = []
		self.conditions = dict()

		# FIXME: move that to config validation on startup
		for k, v in self.configuration['filter'].items():
			if v is not None:
				self.conditions[k] = v
		assert len(self.conditions.keys()) > 0
		self.key_name = self.configuration['data']['key_name']
		assert self.key_name in self.configuration['filter'].keys()
		log.debug("Conditions that will be used for filtering signals are %s", self.conditions, level=2)

	def run(self):
		log.debug("Starting Netfilter thread", level=1)
		self.running = True
		log.debug("Filter connections are %s", self.conditions, level=1)

		while self.running:
			x = self.event_queue.get()
			if x is None:
				break

			process = True
			for (key, val) in self.conditions.items():
				if key in ['dst_port', 'src_port', 'nat_port']:
					res = bool(int(x[key]) == val)
				else:
					res = bool(x[key] == val)
				if res is False:
					log.debug("Packet %s is not matching filter %s=%s - ignoring", x, key, val, level=10)
					process = False
					break

			if process is False:
				continue
			else:
				log.debug("Packet %s is matching  filter", x, level=4)
			if x['sig_type'] == 'new':
				with self.shared_data_lock:
					self.shared_data.update({x[self.key_name]: x})

				self.shared_statistics['shared_data_size'] = len(self.shared_data)
				self.shared_statistics['number_of_created_items'] = self.shared_statistics['number_of_created_items'] + 1
				log.debug("NEW signal %s:%s -> %s:%s -> %s:%s at %s", x['src_ip'], x['src_port'], x['nat_ip'], x['nat_port'], x['dst_ip'], x['dst_port'], x['time'], level=1)
				log.debug("After adding new element, length of shared dict is %i", len(self.shared_data), level=4)

			elif x['sig_type'] == 'destroy':
				log.debug("DESTROY signal %s -> %s:%s -> %s:%s at %s", x['src_ip'], x['nat_ip'], x['nat_port'], x['dst_ip'], x['dst_port'], x['time'], level=1)
				if x[self.key_name]in self.shared_data:
					timer = threading.Timer(self.configuration['data']['del_delay'], self.del_entry, (x[self.key_name], ))
					timer.start()
					self.timer_list.append(timer)

					log.debug("Starting the timer for %i sec to delete the entry %s -> %s:%s -> %s:%s at %s", self.configuration['data']['del_delay'], x['src_ip'], x['nat_ip'], x['nat_port'], x['dst_ip'], x['dst_port'], x['time'], level=4)
				else:
					log.warning("Couldn't find the entry %s in the shared dictionary", x[self.key_name])

			else:
				log.debug("Signal is not of type new or destroy for packet %s - ignoring", x, level=10)

	def del_entry(self, key_value):
		x = self.shared_data[key_value]
		with self.shared_data_lock:
			del self.shared_data[key_value]
		log.debug("DELETED the entry %s -> %s:%s -> %s:%s at %s", x['src_ip'], x['nat_ip'], x['nat_port'], x['dst_ip'], x['dst_port'], x['time'], level=1)
		self.shared_statistics['number_of_deleted_items'] = self.shared_statistics['number_of_deleted_items'] + 1

	def stop(self):
		log.debug("Stopping Netfilter thread", level=1)

		if len(self.timer_list) > 0:
			log.debug("Stopping timer %i that is running in QueueWorker thread", len(self.timer_list), level=2)
			for timer in self.timer_list:
				timer.cancel()

		else:
			log.debug("No timer to stop in Netfilter thread", level=1)

		self.running = False
		self.event_queue.put(None)
