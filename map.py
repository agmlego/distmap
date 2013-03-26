#!/usr/bin/env python

from __future__ import with_statement
from pprint import pprint
from pymaps import Map, Icon, PyMap
import apachelog
import os.path
import GeoIP
import sys

users = {}
mirrors = ('archlinux', 'centos', 'cygwin', 'debian', 'debian-cd', 'fedora', 'gentoo', 'iso', 'kernel', 'pub', 'raspbian', 'slackware', 'ubcd', 'ubuntu', 'ubuntu-releases', 'unity')
mirror_use = {}
skipped_http = []
skipped_ftp = []
skipped_rsync = []

GEOIP_DB = "/usr/local/share/GeoIP/GeoIPCity.dat"
APACHE_LOG = '/var/log/apache2/access.log'
VSFTPD_LOG = '/var/log/vsftpd/access.log'
RSYNCD_LOG = '/var/log/rsyncd/access.log'
OUTPUT_HTML = '/var/www/default/html/map/map.html'

HOME_LATLONG = (47.1544,-88.6471)
GMAP_API_KEY = ''

def sizeof_fmt(num):
	if num < 1024:
		return "%3d bytes"%num
	num /= 1024.0
	for x in ['KB','MB','GB','TB']:
		if num < 1024.0:
			return "%6.3f%s" % (num, x)
		num /= 1024.0

def add_data(protocol,ip,arch,bytes):
	if bytes == '0':
		return

	if ip.startswith('::ffff:') and '.' in ip:
		ip = ip[7:]
	gi = GeoIP.open(GEOIP_DB,GeoIP.GEOIP_STANDARD)
	gir = gi.record_by_addr(ip)
	try:
		loc = (gir['latitude'],gir['longitude'])
	except TypeError:
		if ip not in skipped_http:
			if protocol == 'http':
				skipped_http.append(ip)
		if ip not in skipped_ftp:
			if protocol == 'ftp':
				skipped_ftp.append(ip)
		if ip not in skipped_rsync:
			if protocol == 'rsync':
				skipped_rsync.append(ip)
#		print '(%4s) %15s: %12s -- %s SKIPPED!'%(protocol,ip,bytes,arch)
		return

	if arch == 'pub':
		arch = 'fedora'
	if arch == 'iso':
		arch = item.replace('/iso','')[item.find('/')+1:item.find('/',item.find('/')+1)] + ' iso'
	if arch in mirrors:
		if loc not in users.keys():
			users[loc] = {}
	#		print 'New location! %s'%str(loc)
		if arch not in users[loc].keys():
			users[loc][arch] = {}
	#		print 'New Arch! %s'%arch
		if ip not in users[loc][arch]:
			users[loc][arch][ip] = int(bytes)
#			print '(%4s) %15s: %12s -- %s'%(protocol,ip,bytes,arch)
			if arch not in mirror_use:
				mirror_use[arch] = 0
			else:
				mirror_use[arch] += 1
		else:
			users[loc][arch][ip] += int(bytes)



## HTTP from apache2/access.log ##
format = r'%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"'
p = apachelog.parser(format)
with open(APACHE_LOG) as log:
	lines = log.readlines()
	for line in lines[0:]:
		data = p.parse(line)
		status = data['%>s']
		if not (status.startswith('2') or status.startswith('3')):
			continue

		bytes = data['%b']
		if bytes == '-':
			bytes = '0'

		item = data['%r']
		arch = item[item.find('/')+1:item.find('/',item.find('/')+1)]

		ip = data['%h']
		add_data('http',ip,arch,bytes)
## END HTTP data ##

## FTP from vsftpd/access.log ##
with open(VSFTPD_LOG) as log:
	lines = log.readlines()
	for line in lines[0:]:
		if "OK DOWNLOAD" not in line:
			continue
		ip = line[line.find('"')+1:line.find('"',line.find('"')+1)]
		arch = line[line.find('"/')+2:line.find('/',line.find('"/')+2)]
		if ' bytes' in line:
			bytes = line[line.rfind('", ')+3:line.rfind(' bytes')]
		else:
			bytes = '0'
		add_data('ftp',ip,arch,bytes)
## END FTP data ##

## RSYNC from rsyncd/access.log ##
with open(RSYNCD_LOG) as log:
	lines = log.readlines()
	xfers = {}
	id = 0
	for line in lines[0:]:
		if line.startswith(':'):
			if id in xfers:
				del xfers[id]
			continue
		id = int(line[line.find('[')+1:line.find(']')])
		if 'connect from' in line:
			ip = line[line.find('(')+1:line.find(')')]
			xfers[id] = {'ip':ip}
		if id in xfers:
			if 'rsync on' in line:
				arch = line[line.find('on ')+3:line.find(' from')]
				arch = arch[:arch.find('/')]
				xfers[id]['arch'] = arch
			if 'failed' in line:
				del xfers[id]
				continue
			if 'sent' in line:
				bytes = line[line.find('sent ')+5:line.find(' bytes')]
				add_data('rsync',xfers[id]['ip'],xfers[id]['arch'],bytes)
				del xfers[id]
## END RSYNC data ##

message = '%d locations, skipped %d HTTP %d FTP %d RSYNC'%(len(users),len(skipped_http),len(skipped_ftp),len(skipped_rsync))
print message
print '-'*len(message)
for mirror in sorted(mirror_use.keys()):
	print '\t%s: %d users'%(mirror,mirror_use[mirror])

sum=0
for loc in users:
	for arch in users[loc]:
		for ip in users[loc][arch]:
			sum += 1
print '-'*len(message)
print '%d unique users by IP.'%sum

if '--no-map' in sys.argv:
	sys.exit(0)
# Create a map - pymaps allows multiple maps in an object
tmap = Map()
tmap.zoom = 3

icon = Icon()

for loc in users:
	pointhtml = '<div class="bubble"><ul>'
	for arch in users[loc]:
		sum = 0
		for ip in users[loc][arch]:
			sum += users[loc][arch][ip]
		pointhtml += '<li><strong>%s</strong>: %s, %s'%(arch,(('%d users','%d user')[len(users[loc][arch])==1])%len(users[loc][arch]),sizeof_fmt(sum))

	pointhtml += '</ul>'
	# Add the point to the map
	point = (loc[0], loc[1], pointhtml, icon.id)

	tmap.setpoint(point)

tmap.center = HOME_LATLONG

gmap = PyMap(key=GMAPS_API_KEY, maplist=[tmap])
gmap.addicon(icon)

# pymapjs exports all the javascript required to build the map!
mapcode = gmap.pymapjs()

# Do what you want with it - pass it to the template or print it!
with open(OUTPUT_HTML,'wb') as f:
	mapcode = '<html><head>%s</head><body onload="load()" onunload="GUnload()">\n<div id="map" style="width: 100%%; height: 100%%"></div>\n</body></html>'%mapcode
	f.write(mapcode)
