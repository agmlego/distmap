distmap
=======

I wrote this in one evening several years ago to map out all the userbase of http://lug.mtu.edu. It scrapes the apache, vsftpd, and rsyncd logs to put the lists of distributions and transfer totals onto a map by GeoIP-located unique IP.

You can see the original at http://lug.mtu.edu/map.

Putting it up on github because people on IRC told me to. ;-P

Prerequisites
=============

* pymaps
* apachelog
* GeoIP (and a local database therefor)

TODO
====
* IPv6 addresses seem to choke it, I cannot remember why at the moment.
* Some form of charting or data tracking beyond the last 24 hours would be nice (24 hours may be solely based on our logrotate schedule)
* Not putting all the points into the generated map page source would be good. Takes forever to load on slower connections or browsers with shitty JS engines
