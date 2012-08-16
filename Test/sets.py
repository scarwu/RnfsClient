#!/usr/bin/env python
# -*- coding: utf-8 -*-

c = set(['a', 'b', 'c', 'd'])
l = set(['b', 'd', 'e', 'g'])
s = set(['c', 'd', 'f', 'g'])

ld = c.intersection(l).difference(s)
sd = c.intersection(s).difference(l)
fu = l.difference(c.union(s))
fd = s.difference(c.union(l))

print "     cache: %r" % c
print "     local: %r" % l
print "    server: %r" % s
print ''
print "(L) delete: %r" % ld
print "(S) delete: %r" % sd
print "    upload: %r" % fu
print "  download: %r" % fd
