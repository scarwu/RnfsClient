#!/usr/bin/env python
# -*- coding: utf-8 -*-

c = set(['a', 'b', 'c'])
l = set(['a', 'b', 'd'])
s = set(['b', 'c', 'f'])

de = c.difference(s).union(c.difference(l))
ul = l.difference(c).union(l.difference(s))
dl = s.difference(c).union(s.difference(l))

ld = ul.intersection(de)
sd = dl.intersection(de)

fu = ul.difference(de)
fd = dl.difference(de)

print "         cache: %r" % c
print "         local: %r" % l
print "        server: %r" % s
print ''
print "        delete: %r" % de
print "        upload: %r" % ul
print "      download: %r" % dl
print ''
print "  local delete: %r" % ld
print " server delete: %r" % sd
print "  final upload: %r" % fu
print "final download: %r" % fd
