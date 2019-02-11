#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import socketserver
import wsgiref
import wsgiref.simple_server
import ipaddress
import json
import copy
import falcon

try:
	import cygnuslog  # pylint: disable=unused-import
except ImportError:
	pass

from . import base_thread

log = logging.getLogger("cygnus.pynatconnd")

app = falcon.API()


class ThreadingWSGIServer(socketserver.ThreadingMixIn, wsgiref.simple_server.WSGIServer):
	pass


class NoLoggingWSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler, object):  # pylint:disable=too-few-public-methods
	"""WSGIRequestHandler that logs to debug instead of stderr"""
	def log_message(self, _, *args):
		# pylint:disable=W1401
		"""Log an arbitrary message to log.debug
		"""
		# pylint:enable=W1401
		log.debug("HTTP server request %s - status %s - length %s", *args, level=4)


class BaseHandler(object):  # pylint:disable=too-few-public-methods
	def __init__(self, shared_resources):
		log.debug("Initializing BaseHandler class", level=2)
		self.shared_data = shared_resources['data']
		self.shared_data_lock = shared_resources['lock']
		self.shared_statistics = shared_resources['statistics']
		self.configuration = shared_resources['conf']

	def check_acl(self, addr):
		ip = ipaddress.IPv4Address(addr)
		for x in self.configuration['http_server']['ip_acl']:
			net = ipaddress.IPv4Network(x)
			if ip in net:
				return True
		return False


class GetConnDetails(BaseHandler):  # pylint:disable=too-few-public-methods
	def on_get(self, req, resp, key_value, key_name):
		log.debug("Got GET request for %s from %s", req.path, req.remote_addr, level=2)
		self.shared_statistics['http_stat']['no_of_requests'] += 1
		try:
			if not self.check_acl(req.remote_addr):
				self.shared_statistics['http_stat']['unauthorized_requests'] += 1
				log.error("GET request from an ip %s outside the permitted ip", req.remote_addr)
				resp.content_type = "text/html"
				resp.body = "Forbidden"
				resp.status = falcon.HTTP_403

			elif not key_name == self.configuration['data']['key_name']:
				self.shared_statistics['http_stat']['bad_requests'] += 1
				log.error("Mismatch in key_name betweeen requesting key_name:'%s' and available key_name: '%s'", key_name, self.configuration['data']['key_name'])
				resp.content_type = "text/html"
				resp.body = "Mismatch"
				resp.status = falcon.HTTP_400

			else:
				with self.shared_data_lock:
					if int(key_value) in self.shared_data:
						x = copy.deepcopy(self.shared_data[int(key_value)])
						log.debug("Found a connection matching the requirement %s -> %s:%s -> %s:%s at %s", x['src_ip'], x['nat_ip'], x['nat_port'], x['dst_ip'], x['dst_port'], x['time'], level=2)
					else:
						log.info("No connection details found for given key value %s", key_value)
						x = None

				if not x:
					self.shared_statistics['http_stat']['unsuccessful_replies'] += 1
					resp.content_type = "text/html"
					resp.body = "Not found"
					resp.status = falcon.HTTP_404
				else:
					self.shared_statistics['http_stat']['successful_replies'] += 1
					resp.body = json.dumps(x, sort_keys=True, indent=4)
					resp.content_type = "application/json"
					resp.status = falcon.HTTP_200

			log.debug("Finished GET request on Get_conn_details for %s", req.path, level=4)

		except falcon.HTTPError as e:
			log.error("HTTPError occured in DeliverThread with status %s title %s", e.status, e.title, exc_info=True)
			raise
		except Exception as e:
			log.error("Exception occured in DeliverThread with message %s", e, exc_info=True)
			raise falcon.HTTPInternalServerError(title="Internal server error", description="Generic exception for status path %s" % req.path)


class DebugNatconnd(BaseHandler):  # pylint:disable=too-few-public-methods
	def on_get(self, req, resp):
		log.debug("Got GET request for %s from %s", req.path, req.remote_addr, level=2)
		if not self.check_acl(req.remote_addr):
			log.error("GET request to /debug from an ip %s outside the permitted ip", req.remote_addr)
			resp.content_type = "text/html"
			resp.body = "Forbidden"
			resp.status = falcon.HTTP_403

		else:
			with self.shared_data_lock:
				log_dict = copy.deepcopy(self.shared_data)

			resp.body = json.dumps(log_dict, sort_keys=True, indent=4)
			resp.content_type = "application/json"
			resp.status = falcon.HTTP_200


class NagiosViewer(BaseHandler):  # pylint:disable=too-few-public-methods
	def on_get(self, req, resp):
		log.debug("Got GET request for %s from %s", req.path, req.remote_addr, level=2)
		if not self.check_acl(req.remote_addr):
			log.error("GET request to /nagios from an ip %s outside the permitted ip", req.remote_addr)
			resp.content_type = "text/html"
			resp.body = "Forbidden"
			resp.status = falcon.HTTP_403
		else:
			resp.body = json.dumps(self.shared_statistics, sort_keys=True, indent=4)
			resp.content_type = "application/json"
			resp.status = falcon.HTTP_200


class HTTPServer(base_thread.BaseThread):
	def __init__(self, shared_resources, host):
		assert 'ip' in host and 'port' in host
		base_thread.BaseThread.__init__(self, shared_resources['statistics'])
		log.debug("Initializing HTTP server thread")
		self.setName('HTTPServer')
		self.configuration = shared_resources['conf']
		get_conn_details = GetConnDetails(shared_resources)
		app.add_route('/{key_name}/{key_value}', get_conn_details)

		debug_natconnd = DebugNatconnd(shared_resources)
		app.add_route('/debug', debug_natconnd)

		nagios_viewer = NagiosViewer(shared_resources)
		app.add_route('/nagios', nagios_viewer)

		self.http_serv = wsgiref.simple_server.make_server(host['ip'], host['port'], app, server_class=ThreadingWSGIServer, handler_class=NoLoggingWSGIRequestHandler)
		log.debug("Initializing http_server thread Complete at %s:%s", host['ip'], host['port'])

	def run(self):
		self.running = True
		log.debug("Starting http_server thread")
		self.http_serv.serve_forever()

	def stop(self):
		log.debug("Stopping http_server thread")
		self.running = False
		self.http_serv.shutdown()
