#!/usr/bin/env python
#
# Copyright (c) 2013, Andrew G. Meyer
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met: 
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer. 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution. 
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies, 
# either expressed or implied, of the distmap project.

from __future__ import with_statement
from pprint import pprint

import cPickle as pickle

import pygmaps
import apachelog
import os.path
import geoip2.database
import geoip2.errors
import sys
from termcolor import cprint

users = {}
mirrors = ('archlinux', 'centos', 'cygwin', 'debian', 'debian-cd', 'fedora',
           'gentoo', 'iso', 'kernel', 'pub', 'raspbian', 'slackware', 'tails',
           'ubcd', 'ubuntu', 'ubuntu-releases', 'unity')
mirror_use = {}
skipped_http = []
skipped_ftp = []
skipped_rsync = []

GEOIP_DB = "logs/GeoLite2-City.mmdb"
APACHE_LOG = 'logs/nginx-access.log'
VSFTPD_LOG = 'logs/vsftp-access.log'
RSYNCD_LOG = 'logs/rsync-access.log'
OUTPUT_HTML = 'logs/map.html'
SUMMARY_FILE = 'logs/summary.txt'

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
    gi = geoip2.database.Reader(GEOIP_DB)
    try:
        gir = gi.city(ip)
        loc = (gir.location.latitude,gir.location.longitude)
        if None in loc:
            raise geoip2.errors.AddressNotFoundError('Not good')
    except geoip2.errors.AddressNotFoundError:
        if ip not in skipped_http:
            if protocol == 'http':
                skipped_http.append(ip)
        if ip not in skipped_ftp:
            if protocol == 'ftp':
                skipped_ftp.append(ip)
        if ip not in skipped_rsync:
            if protocol == 'rsync':
                skipped_rsync.append(ip)
        cprint('(%4s) %15s: %12s -- %s SKIPPED!i Address not found.'%(protocol,ip,bytes,arch),'red')
        return

    if arch == 'pub':
        arch = 'fedora'
    if arch == 'iso':
        arch = item.replace('/iso','')[item.find('/')+1:item.find('/',item.find('/')+1)] + ' iso'
    if arch in mirrors:
        if loc not in users.keys():
            users[loc] = {}
            #cprint('New location! %s'%str(loc),'green')
        if arch not in users[loc].keys():
            users[loc][arch] = {}
            #cprint('New Arch! %s'%arch,'yellow')
        if ip not in users[loc][arch]:
            users[loc][arch][ip] = int(bytes)
            color = ('blue','cyan')[':' in ip]
            cprint('(%4s) %15s: %12s -- %s'%(protocol,ip,bytes,arch),color)
            if arch not in mirror_use:
                mirror_use[arch] = 0
            else:
                mirror_use[arch] += 1
        else:
            try:
                users[loc][arch][ip] += int(bytes)
            except ValueError:
                if ip not in skipped_http:
                    if protocol == 'http':
                        skipped_http.append(ip)
                if ip not in skipped_ftp:
                    if protocol == 'ftp':
                        skipped_ftp.append(ip)
                if ip not in skipped_rsync:
                    if protocol == 'rsync':
                        skipped_rsync.append(ip)
                cprint('(%4s) %15s: %12s -- %s SKIPPED! Bad line in log.'%(protocol,ip,bytes,arch),'magenta')
                return

if '--no-parse' in sys.argv:
    users = pickle.load(open('users.pkl'))
    mirror_use = pickle.load(open('mirror_use.pkl'))
    skipped_http = pickle.load(open('skip_http.pkl'))
    skipped_ftp = pickle.load(open('skip_ftp.pkl'))
    skipped_rsync = pickle.load(open('skip_rsync.pkl'))
else:
    
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
    pickle.dump(users,open('users.pkl','wb'))
    pickle.dump(mirror_use,open('mirror_use.pkl','wb'))
    pickle.dump(skipped_http,open('skip_http.pkl','wb'))
    pickle.dump(skipped_ftp,open('skip_ftp.pkl','wb'))
    pickle.dump(skipped_rsync,open('skip_rsync.pkl','wb'))

with open(SUMMARY_FILE,'wb') as f:
    message = []
    message.append('%d locations, skipped %d HTTP %d FTP %d RSYNC'%(len(users),len(skipped_http),len(skipped_ftp),len(skipped_rsync)))
    message.append('-'*len(message))
    for mirror in sorted(mirror_use.keys()):
        message.append('\t%s: %d users'%(mirror,mirror_use[mirror]))
    
    sum=0
    for loc in users:
        for arch in users[loc]:
            for ip in users[loc][arch]:
                sum += 1
    message.append('-'*len(message))
    message.append('%d unique users by IP.'%sum)

    message = '\n'.join(message)

    f.write(message)
    print message

if '--no-map' in sys.argv:
    sys.exit(0)

tmap = pygmaps.maps(HOME_LATLONG[0],HOME_LATLONG[1],3)

for loc in users:
    pointhtml = '<div class="bubble"><ul>'
    for arch in users[loc]:
        sum = 0
        for ip in users[loc][arch]:
            sum += users[loc][arch][ip]
        pointhtml += '<li><strong>%s</strong>: %s, %s'%(arch,(('%d users','%d user')[len(users[loc][arch])==1])%len(users[loc][arch]),sizeof_fmt(sum))

    pointhtml += '</ul>'
    # Add the point to the map
    if None not in loc:
        tmap.addpoint(loc[0], loc[1], color='#0000FF', title=pointhtml)

tmap.draw(OUTPUT_HTML)
