#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
import re
	
def counter(count, message='', step=1000,):
	if count % step == 0:
		sys.stderr.write("\r\t{:,d}{}".format(count,message))

dic = {}
count = 0
for line in iter(sys.stdin.readline, ""):
	array = line.split()
	if len(array) != 3:
		continue
	if not 'unknown' in array[2] and not 'CD' in array[1]:
		m = re.match(r'^[\W0-9]+$', array[0])
		if not m:
			count += 1
			key = '\t'.join(array)
#			print(key)
			dic[key] = dic.get(key,0) + 1
			entry = key + '\t' + str(dic[key])
			counter(count,' words counted ...')
#			print(entry)
sys.stderr.write("\n\t{:,d} entries will go to stout\n".format(len(dic)))
count = 0
for k,v in dic.items():
	count += 1
	entry = k + '\t' + str(v)
	counter(count, ' entries ...')
	print(entry)
sys.stderr.write("\n\t{:,d} entries finished\n".format(count))
