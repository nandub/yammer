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


from InstallSettings import settings
import os, commands, sys
import threading, textwrap

def getVersionString():
  return settings['version'] + '.' + getBuildNum()

def getBuildInfo():
  fp= open(settings['yammerRoot'] + '/buildnum')
  buildnum= fp.readline()
  fp.close()
  return buildnum.strip().split('|')

def getUpdateDate():
  return getBuildInfo()[0]

def getBuildNum():
  return getBuildInfo()[1]

_wrapper= textwrap.TextWrapper(initial_indent=' '*2,
    subsequent_indent=' '*4)

def debugMessage(message):
  ct= threading.currentThread()
  mensaje= '%s: %s' % (ct, message)
  if len(mensaje) > 70 or '\n' in mensaje:
    mensaje= '%s: {\n' % ct
    mensaje += '\n'.join(
        [_wrapper.fill(' '.join([l.strip()
          for l in submessage.split('\n')]))
          for submessage in message.split('\n\n')])
    mensaje += '\n}\n'
  print mensaje
  sys.stdout.flush()
