# Copyright 2002, 2004 John T. Reese.
# email: jtr at ofb.net
# 
# This file is part of Yammer.
# 
# Yammer is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# Yammer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Yammer; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import sys, os, string, time
from InstallSettings import settings
import YOS, glob, Gale
from pygale.pygale import *
import pygale.authcache

def havePrivateFor(recp):
  return authcache.have_a_privkey([recp])

def privRoot():
  return os.environ['HOME'] + "/.gale/auth/private/"

def privPath(recp):
  path= privRoot() + recp
  if os.path.exists(path):
    return path
  path= path + ".gpri"
  if os.path.exists(path):
    return path
  return None

def getFullname(keyname):
  n, k= lookup_location(keyname, do_akd=False)
  if not isinstance(k, (tuple, list)) or not hasattr(k[0], 'comment'):
    return '?? %r ??' % k
  return k[0].comment()

def userFromKey(key):
  key= os.path.basename(key)
  if len(key) > 5 and key[-5:] == '.gpri':
    key= key[:-5]
  return key

# returns a tuple: signed time/expire time, or None if the key is too
# old to have these fields
def getKeyTime(key):
  p= privPath(key)
  return os.stat(p).st_mtime

def listPrivateUsers():
  privs= []
  for domain in settings['galeDomains'].split():
    privs += glob.glob(privRoot() + "*@" + domain)
    privs += glob.glob(privRoot() + "*@" + domain \
      + ".gpri")
  return map(userFromKey, privs)

def pubPath(recp):
  path= os.environ['HOME'] + "/.gale/auth/local/" + recp
  if os.path.exists(path):
    return path
  path= privRoot() + recp + ".gpub"
  if os.path.exists(path):
    return path
  return None

def gkgen(id, name, source=None):
  from YGaleClient import YGaleClient
  if string.find(id, '@') == -1:
    raise 'nodomain'
  error= ''
  gkf= YOS.psafepopen(['gkgen', id, '/' + name], 'r')
  while 1:
    line= gkf.readline()
    if not line: break
    error= error + line
  if gkf.close() == 0:
    try:
      yg= YGaleClient()
      msg= 'new key: %(id)s %(name)s' % locals()
      if source is not None:
        msg += ' (via %s)' % source
      yg.gsend(id, ['_gale.notice.' + id], msg)
    except:
      pass
    return
  else:
    return error
