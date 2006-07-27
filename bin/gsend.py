#!/usr/bin/env python

from pygale import pygale, prettypuff, gale_env, version
import sys, getopt, string, os, time
try:
	import readline
except:
	print 'No readline module found; line-editing capabilities unavailable'

# Default behavior
RETURN_RECEIPT = 0

def usage(arg):
	print 'gsend.py version %s' % version.VERSION
	print "Usage: %s [-pPd] location [location ...] [/keyword...]" % arg
	print 'Flags:    -p        always request receipt'
	print '          -P        never request receipt'
	print '          -d        enable PyGale debugging'
	print '          -v        show version'

def print_msg(msg):
	date = time.strftime('%m-%d %H:%M:%S ',
		time.localtime(time.time()))
	msg = date + string.strip(msg)
	print msg

def enter_puff():
	text = ''
	while 1:
		try:
			line = raw_input()
		except EOFError:
			break
		except KeyboardInterrupt:
			print 'Message aborted.'
			sys.exit(0)
		if line == '.':
			break
		text = text + line + '\r\n'
	return text

def sendpuff(locs, keywords):
	# Look up locations
	ret = pygale.lookup_all_locations(locs)
	send_locs = []
	bad_locs = []
	encr_recipients = []
	for (loc, recps) in ret:
		if recps is None:
			bad_locs.append(loc)
		else:
			send_locs.append(loc)
			encr_recipients = encr_recipients + recps
	if bad_locs:
		print 'Error: no valid recipients'
		sys.exit(-1)
	if '' in encr_recipients:
		# null key
		encr_recipients = []
	
	# Print the header
	bolded_locs = map(prettypuff.bold_location, send_locs)
	header = 'To: %s' % string.join(bolded_locs, ' ')
	if keywords:
		bolded_keywords = map(prettypuff.bold_keyword, keywords)
		bolded_keywords = map(lambda x: '/' + x, bolded_keywords)
		header = header + ' ' + string.join(bolded_keywords, ' ')
	print header
	print '(End your message with EOF or a solitary dot.)'

	# Get the puff text
	pufftext = enter_puff()

	# Construct puff
	signer = pygale.gale_user()
	puff = pygale.Puff()
	gfrom = gale_env.get('GALE_NAME',
		gale_env.get('GALE_FROM', 'PyGale user'))
	puff.set_loc(string.join(locs, ' '))
	puff.set_text('message/sender', gfrom)
	puff.set_time('id/time', int(time.time()))
	puff.set_text('id/class', 'gsend.py/%s' % version.VERSION)
	puff.set_text('id/instance', pygale.getinstance())
	if RETURN_RECEIPT:
		puff.set_text('question.receipt', signer)
	if keywords:
		for keyw in keywords:
			puff.set_text('message.keyword', keyw)
	puff.set_text('message/body', pufftext)

	# Sign
	ret = puff.sign_message(signer)
	if ret is None:
		# unable to sign
		signed_puff = puff
	else:
		signed_puff = ret

	# Encrypt
	if encr_recipients:
		ret = signed_puff.encrypt_message(encr_recipients)
		if ret is None:
			# unable to encrypt
			encrypted_puff = signed_puff
		else:
			encrypted_puff = ret
	else:
		encrypted_puff = signed_puff
	
	# Create gale connection
	c = pygale.GaleClient()
	c.connect()
	c.transmit_puff(encrypted_puff)
	print 'Message sent.'

def main():
	global RETURN_RECEIPT
	opts, args = getopt.getopt(sys.argv[1:], 'pPd:v')
	for (opt, val) in opts:
		if opt == '-P':
			RETURN_RECEIPT = 0
		elif opt == '-p':
			RETURN_RECEIPT = 1
		elif opt == '-d':
			pygale.DEBUG = int(val)
		elif opt == '-v':
			usage(sys.argv[0])
			sys.exit(0)
		else:
			usage(sys.argv[0])
			print 'Unknown option:', opt
			sys.exit(0)

	# Initialize PyGale before processing locations
	pygale.init()
	sys.exitfunc = pygale.shutdown
	pygale.set_error_handler(print_msg)
	pygale.set_update_handler(print_msg)

	if not gale_env.get('GALE_DOMAIN', None):
		print 'Please run pygale-config to set up your PyGale environment.'
		sys.exit(0)

	# Extract locations and keywords from cmdline args
	locs = filter(lambda x: x[0] != '/', args)
	# default domain and alias expansion
	locs = map(pygale.expand_aliases, locs)
	keywords = map(lambda x: x[1:], filter(lambda x: x[0] == '/', args))
	if not locs:
		usage(sys.argv[0])
		sys.exit()
	
	# Send it
	try:
		sendpuff(locs, keywords)
	except KeyboardInterrupt:
		sys.exit(0)

if __name__ == '__main__':
	main()


