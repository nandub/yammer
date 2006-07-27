#!/usr/bin/env python

# A simple gsub client
# Does not respond to AKD requests

import sys, getopt, time, string
from pygale import pygale, prettypuff, gale_env, version

def usage(arg):
	print 'gsub.py version %s' % version.VERSION
	print "Usage: %s location [location ...]" % arg

def print_msg(msg):
	date = time.strftime('%m-%d %H:%M:%S ',
		time.localtime(time.time()))
	msg = date + string.strip(msg)
	print msg

def my_own_personal_show(puff):
	recipients = puff.get_recipients()
	print 'recipients: ' + string.join([`x` for x in recipients])
	return prettypuff.show(puff)

def recvpuffs(sub, quiet):
	conn = pygale.GaleClient()
	conn.set_onconnect(lambda host, c=conn, s=sub, q=quiet:
		on_connect(host, c, s, q))
	host = conn.connect()
	if host is None:
		print 'Unable to connect to a gale server'
		return
	conn.set_puff_callback(my_own_personal_show)
	#conn.set_puff_callback(prettypuff.show)

	# loop forever
	conn.next()

def on_connect(host, conn, sub, quiet):
	print_msg('Connected to %s' % host)

	if not quiet:
		sender = gale_env.get('GALE_FROM', 'Unknown sender')
		pygale.notify_in('in.present', conn, fullname=sender)
		pygale.notify_out('out.disconnected', conn, fullname=sender)

	# Subscribe to a list of locations
	# Add in our location if not there
	myid = pygale.gale_user()
	if myid not in sub:
		sub.append(myid)
	bad, good = conn.sub_to(sub)
	if bad:
		for b in bad:
			print_msg('Unable to find location %s' % b)
	if not good:
		print_msg('No locations found')
		sys.exit(-1)
	else:
		for g in good:
			print_msg('Subscribed to %s' % g)

if __name__ == '__main__':
	opts, args = getopt.getopt(sys.argv[1:], 'd:av')
	quiet = 0
	for opt, val in opts:
		if opt == '-d':
			pygale.DEBUG = int(val)
		elif opt == '-a':
			quiet = 1
		elif opt == '-v':
			usage(sys.argv[0])
			sys.exit()
	if len(args) < 1:
		usage(sys.argv[0])
		sys.exit()
	
	pygale.init()
	sys.exitfunc = pygale.shutdown
	pygale.set_error_handler(print_msg)
	pygale.set_update_handler(print_msg)
	try:
		recvpuffs(args, quiet)
	except KeyboardInterrupt:
		sys.exit(0)
