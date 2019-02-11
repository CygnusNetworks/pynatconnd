#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

from natconnd.nfct_cffi import NFCT  # pylint: disable=no-name-in-module


setup(
	name='pynatconnd',
	version='0.15',
	author='Senthil Kumar, Dr. Torge Szczepanek',
	author_email='debian@cygnusnetworks.de',
	license='Apache-2.0',
	keywords=['nat', 'tracking', 'nfct', 'conntrack', 'flow', 'connection', 'traffic', 'analysis', 'analyze', 'network', 'linux', 'security', 'track', 'netfilter', 'audit', 'cffi', 'libnetfilter_conntrack', 'netlink', 'socket', 'firewall'],
	description='NAT Connection Tracking Daemon',

	classifiers=[
		'Development Status :: 4 - Beta',
		'Intended Audience :: Developers',
		'Intended Audience :: System Administrators',
		'Intended Audience :: Telecommunications Industry',
		'License :: OSI Approved',
		'Operating System :: POSIX :: Linux',
		'Programming Language :: Python',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 3',
		'Topic :: Security',
		'Topic :: System :: Networking :: Monitoring',
		'Topic :: System :: Operating System Kernels :: Linux'],

	install_requires=['cffi', 'configobj', 'falcon'],
	ext_modules=[NFCT().ffi.verifier.get_extension()],
	packages=['natconnd'],
	entry_points={'console_scripts': ['pynatconnd = natconnd.daemon:main']}
)
