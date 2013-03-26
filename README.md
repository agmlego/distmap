distmap
=======

I wrote this in one evening to map out all the userbase of http://lug.mtu.edu. It scrapes the apache, vsftd, and rsyncd logs to put the lists of distributions and transfer totals onto a map by GeoIP-located unique IP.

You can see the original at http://lug.mtu.edu/map.

Putting it up on github because people on IRC told me to. ;-P

Prerequisites
=============

* pymaps
* apachelog
* GeoIP (and a local database therefor)
