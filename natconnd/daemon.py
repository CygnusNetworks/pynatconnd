#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import queue
import threading
import sys
import argparse
import time
import logging
import logging.handlers

try:
	import cygnuslog  # pylint: disable=unused-import
except ImportError:
	pass

from . import pynatconnd_config
from . import http_server
from . import queue_worker
from . import net_filter
from . import garbage_collection

log = logging.getLogger('cygnus.pynatconnd')


def main():  # pylint:disable=too-many-locals,too-many-statements
	log.info("Starting Pynatconnd")
	try:
		argp = argparse.ArgumentParser()
		argp.add_argument("-c", "--config", help="config file name", default='/etc/pynatconnd.conf')
		argp.add_argument("-l", "--log-level", help="Log Debug level", type=int, default=None)
		argp.add_argument("-i", "--ip", help="IP to bind to", type=str, default=None)
		argp.add_argument("-p", "--port", help="Port to bind to", type=int, default=None)

		args = argp.parse_args()

		config_handler = pynatconnd_config.PynatconndConfig(args.config)
		config = config_handler.get_configobj()
		log.debug("Obtained the configuration file", level=4)

		if callable(getattr(log, "set_facility", None)):
			log.set_facility(int(config["syslog"]["local_facility"]) + logging.handlers.SysLogHandler.LOG_LOCAL0)

			if args.log_level is not None:
				log.set_debug_level(int(args.log_level))
			else:
				log.set_debug_level(int(config["syslog"]["debug_level"]))

		log.debug("Creating an instance of shared data, threading.lock() and a queue", level=6)
		shared_data = dict()
		shared_statistics = dict(queue_size=0, shared_data_size=0, number_of_deleted_items=0, number_of_created_items=0, expired_data=0, http_stat={'no_of_requests': 0, 'unauthorized_requests': 0, 'successful_replies': 0, 'unsuccessful_replies': 0, 'bad_requests': 0})
		data_lock = threading.Lock()
		event_queue = queue.Queue()
		shared_resource = {'data': shared_data, 'statistics': shared_statistics, 'lock': data_lock, 'conf': config}
		join_timeout = config['threading']['join_timeout']

		http_host = dict(ip=None, port=None)
		if args.ip is not None:
			http_host['ip'] = args.ip
		else:
			http_host['ip'] = config["http_server"]["host"]

		if args.port is not None:
			http_host['port'] = int(args.port)
		else:
			http_host['port'] = int(config["http_server"]["port"])

		log.debug("Creating an instance of three threads Receiver, queue_worker and deliver_worker", level=6)
		threads = []
		threads.append(queue_worker.QueueWorker(event_queue, shared_statistics))
		threads.append(net_filter.NetFilter(event_queue, shared_resource))
		threads.append(http_server.HTTPServer(shared_resource, host=http_host))
		threads.append(garbage_collection.GarbageCollectorThread(shared_resource))

		for thread in threads:
			thread.start()

		start_time = time.time()
		shared_statistics['prgm_start_time'] = start_time
		thread_stat = {}
		for thread in threads:
			thread_stat.update({thread.getName(): {'alive_time': thread.alive_time - time.time(), 'is_alive': True if thread.is_alive else False}})
		shared_statistics['threads_stat'] = thread_stat
	except pynatconnd_config.PynatconndConfigException as e:
		print("Error in config file with msg %s" % e)
		sys.exit(0)
	except IOError as e:
		print("IOError occured with message %s" % e)
		sys.exit(0)
	except Exception as e:
		log.error("Error init pynatconnd with msg %s", e, exc_info=True)
		sys.exit(0)

	while True:
		try:
			time.sleep(1)
			for thread in threads:
				if thread.running:
					continue
				else:
					stop_all_threads(threads, join_timeout)
					sys.exit(1)
		except KeyboardInterrupt:
			log.debug("KeyboardInterrupt caught, stopping all threads", level=1)
			stop_all_threads(threads, join_timeout)
			sys.exit(0)


def stop_all_threads(threads, join_timeout):
	threads.reverse()
	for thread in threads:
		thread.stop()

	log.debug("Joining all threads", level=1)

	for thread in threads:
		if thread.is_alive():
			thread.join(timeout=join_timeout)

	log.debug("all threads stopped", level=1)


if __name__ == '__main__':
	main()
