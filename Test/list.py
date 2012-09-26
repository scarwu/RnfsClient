#!/usr/bin/env python

import os
from collections import deque

a = [{'a': 1, 'b': 2}, {'a': 2, 'b': 2}]
b = [{'a': 1, 'b': 2}]

for x in a:
	if x not in b:
		print 'Not', x
	else:
		print 'Yes', x
