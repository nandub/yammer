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
import YOS, glob
from KeyStore import *


# pull in all the pygale functions
from pygale.pygale import *
import pygale.authcache
import pygale


DEBUG= DEBUG_SOCKET

# danger... can this be multiply invoked?
init()

sys.exitfunc= shutdown






def filetraces(message, *args):
  fds= os.listdir('/proc/%s/fd' % os.getpid())
  import YammerUtils
  YammerUtils.debugMessage('%s: %d fds (%s)' %
      (message % args, len(fds), ' '.join(fds)))

# key used to make private messages in the database unreadable (though
# not securely so)
def getObscureKey():
  global k
  if k is None:
    k= [ord(x) & 0x1f for x in "turbomandibulogitis"]
  return k




def obscureString(s):
  lines= s.split('\n')
  s2= []
  ok= getObscureKey()
  okl= len(ok)
  for line in lines:
    s2a= ''
    for i in range(len(line)):
      ol= ord(line[i])
      if ol >= ord(' '):
        ol ^= ok[i % okl]
      s2a += unichr(ol)
    s2.append(s2a)
  return string.join(s2, '\n')


# xor is its own inverse
def deobscureString(s):
  return obscureString(s)





def main():
  print gkgen('test10', 'test of Gale.gkgen')
  gsend('jtr@dev.yammer.net', ['jtr@miskatonic.nu'], 'testing\n')

k= None
if __name__ == '__main__':
  main()

