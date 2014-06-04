distmap
=======

I wrote this in one evening several years ago to map out all the userbase of http://lug.mtu.edu. It scrapes the apache (or nginx, apparently), vsftpd, and rsyncd logs to put the lists of distributions and transfer totals onto a map by GeoIP-located unique IP.

You can see the original at http://lug.mtu.edu/map.

Putting it up on github because people on IRC told me to. ;-P

Prerequisites
=============

* [pygmaps](https://code.google.com/p/pygmaps/)
* [apachelog](https://pypi.python.org/pypi/apachelog/1.0)
* [termcolor](https://pypi.python.org/pypi/termcolor/1.1.0)
* [GeoIP2](http://geoip2.readthedocs.org/en/latest/) (and a [local "GeoLite2 City" database](http://dev.maxmind.com/geoip/geoip2/geolite2/) therefor)

TODO
====
* Some form of charting or data tracking beyond the last 24 hours would be nice (24 hours may be solely based on our logrotate schedule)
* Not putting all the points into the generated map page source would be good. Takes forever to load on slower connections or browsers with shitty JS engines
