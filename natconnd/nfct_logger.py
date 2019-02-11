#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

from xml.etree import ElementTree
from io import BytesIO
import datetime
from collections import namedtuple
import logging

try:
	import cygnuslog  # pylint: disable=unused-import
except ImportError:
	pass

FlowData = namedtuple('FlowData', 'src dst sport dport')
about_FlowData = namedtuple('about', 'ts type proto')
# flow.attrib['type'],ts, proto,


def parse_event(ev_xml):
	log.debug("parse_event function is called with the argument %s", ev_xml, level=10)
	etree = ElementTree.parse(BytesIO(ev_xml))

	flow = next(etree.iter())
	ts = flow.find('when')
	ts = str(datetime.datetime(*(int(ts.find(k).text) for k in ['year', 'month', 'day', 'hour', 'min', 'sec'])))
	flow_data = dict()

	for meta in flow.findall('meta'):
		if meta.attrib['direction'] in ['original', 'reply']:
			l3, l4 = list(map(meta.find, ['layer3', 'layer4']))
			src, dst = (l3.find(k).text for k in ['src', 'dst'])
			proto = l3.attrib['protoname'], l4.attrib['protoname']  # pylint: disable=redefined-variable-type,
			if proto[1] not in ['tcp', 'udp']:
				return
			sport, dport = (int(l4.find(k).text) for k in ['sport', 'dport'])
			flow_data[meta.attrib['direction']] = FlowData(src, dst, sport, dport)
			flow_data['about'] = about_FlowData(ts, proto, flow.attrib['type'])

	# Name of the keys should remain the same. If it has to be changed make sure the values under 'filter'
	# section in configuration file and in workerqueue thread are also changed
	nat_event = {'src_ip': flow_data['original'].src, 'src_port': flow_data['original'].sport,
				'dst_ip': flow_data['original'].dst, 'dst_port': flow_data['original'].dport,
				'nat_ip': flow_data['reply'].dst, 'nat_port': flow_data['reply'].dport,
				'time': flow_data['about'].ts,
				'sig_type': flow_data['about'].proto, 'protocol': flow_data['about'].type}

	log.debug("Returning a dictionary from parse_event function %s", nat_event, level=10)
	return nat_event
