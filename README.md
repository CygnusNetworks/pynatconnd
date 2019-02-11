#pynatconnd

pynatconnd is a connection tracking daemon intended to track Linux netfilter 
connection tracking entries (IP NAT mappings) going through a linux nat firewall 
in a efficient way using libnetfilter_conntrack entries.

It is based on [conntrack-logger](https://github.com/mk-fg/conntrack-logger), but adds
a HTTP REST interface, to allow querying of currently established connection in the NAT table.

It allows you to query currently existing Netfilter NAT entries by a HTTP query to the 
builtin HTTP REST server. One possible usage scenario is, to get the internal (non-masqueraded) 
ip address from external IP:Port combination, if you control the Linux NAT server and run 
pynatconnd on this box.

We are using this, to get the internal IP behind a NAT server, where pynatconnd is deployed 
on the NAT device by using the IP/Port combination presented to a external webserver/proxy (in our case nginx).

For this to work you would need the following config on nginx:

```
proxy_set_header      X-Real-IP $remote_addr;
proxy_set_header      X-Real-Port $remote_port;
```

##Installation

It's a regular package for Python 2.7 and 3.x, so can be
installed from a checkout with something like that:

`python setup.py install`
	
In addition Debian and RPM Packaging is provided in a Debian and RPM Spec file.

## Configuration

The following configuration will track all accesses to internet ip 198.51.100.1 on port 443 (https) coming from 
the external IP 100.64.2.1 of the NAT Linux host running pynatconnd. 
Data can be queried by key nat_port, which is the port on which a connection is established to dst_ip:dst_port.

The http REST server is listening on ip 0.0.0.0 and can be queried by all ips/subnets listed in the ip_acl. 
Be sure to protect this with some firewall rules possibly in addition.

```
[filter]
dst_ip = 198.51.100.1
dst_port = 443
nat_ip = 100.64.2.1

[data]
key_name = nat_port

[http_server]
host = 0.0.0.0
ip_acl = 192.168.248.0/24,127.0.0.1
```

The following filter types are possible:

 * src_ip
 * src_port
 * nat_ip
 * nat_port
 * dst_ip
 * dst_port

One of these can be used as the key_name.

## Requirements

* Python 2.7 or Python 3.x
* [CFFI](http://cffi.readthedocs.org) (for libnetfilter_conntrack bindings)
* [libnetfilter_conntrack](http://www.netfilter.org/projects/libnetfilter_conntrack)
* nf_conntrack_netlink kernel module (e.g. `modprobe nf_conntrack_netlink`)
* Python: falcon and configobj

CFFI uses C compiler to generate bindings, so gcc (or other compiler) should be
available if module is being built from source or used from checkout tree.

To install these requirements on Debian:

`apt install build-essential libnfnetlink-dev python-cffi libnetfilter-conntrack-dev libpython2.7-dev`

In addition the **nf_conntrack_netlink** module must be loaded:

```
modprobe nf_conntrack_netlink
```

