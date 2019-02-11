#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pynatconnd config spec"""
import configobj
import validate


CONFIG_SPEC = r"""
[syslog]
local_facility=integer(min=0,max=7,default=0)
debug_level=integer(min=0,max=10,default=4)

[filter]
src_ip = ip_addr(default=None)
src_port = integer(default=None)
nat_ip = ip_addr(default=None)
nat_port = integer(default=None)
dst_ip = ip_addr(default=None)
dst_port = integer(default=None)

[data]
key_name = string(min=1)
del_delay = float(default=10.0)
garbage_cleaner_interval = float(default=3600.0)
life_span=float(default=3600.0)

[threading]
join_timeout = float(default=5.0)

[http_server]
host = string(min=1, default="127.0.0.1")
port = integer(min=1024, default=8080)
ip_acl = string_list
"""


class PynatconndConfigException(Exception):
	"""Exception class for NetadminConfig class"""
	pass


class PynatconndConfig(object):  # pylint: disable=R0903
	"""Class for reading and parsing Netadmin-Management config."""
	__CONFIG_SPEC = configobj.ConfigObj(CONFIG_SPEC.splitlines(), list_values=False)

	def __init__(self, cfg):
		"""Constructor reading and validating config against given config spec
		@param cfg: optional parameter containing config file
		@type cfg: string"""
		self.config = configobj.ConfigObj(cfg, file_error=True, configspec=self.__CONFIG_SPEC)
		validator = validate.Validator()
		res = self.config.validate(validator, preserve_errors=True)
		for section_list, key, error in configobj.flatten_errors(self.config, res):  # pylint: disable=W0612
			raise PynatconndConfigException("Failed to validate section %s key %s in config file %s" % (", ".join(section_list), key, cfg))

	def get_configobj(self):
		"""Function returning created ConfigObj
		@return: ConfigObj
		@rtype: class
		"""
		return self.config
