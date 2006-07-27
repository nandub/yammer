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


import os, sys, string

def which(cmd):
  if string.find(cmd, '/') != -1 or cmd == '..' or cmd == '.':
    return cmd
  for bindir in string.split(os.environ['PATH'], ':'):
    trialcmd= bindir + '/' + cmd
    if os.path.exists(trialcmd):
      return trialcmd
  raise OSError, 'not in path: ' + cmd

def safesystem(argv):
  kid= os.fork()
  if kid == 0:
    os.execv(argv[0], argv)
  stato= os.waitpid(kid, 0)[1]
  if stato & 0xFF == 0x00:
    return stato >> 8
  else:
    return stato & 0xFF

def psafesystem(argv):
  return safesystem([which(argv[0])] + argv[1:])

def psafepopen(argv, mode):
  return safepopen([which(argv[0])] + argv[1:], mode)

def safepopen(argv, mode):
  if mode != 'r' and mode != 'w':
    raise OSError, 'illegal file mode ' + mode
  pipends= os.pipe()
  kiddup= mode=='r'
  daddup= 1 - kiddup
  kid= os.fork()
  if kid == 0:
    os.dup2(pipends[kiddup], kiddup)
    os.close(pipends[daddup])
    os.execv(argv[0], argv)
  os.close(pipends[kiddup])
  return PipeFile(os.fdopen(pipends[daddup], mode), kid)

class PipeFile:

  def __init__(self, file, pid):
    self.file= file
    self.pid= pid

  def __getattr__(self, name):
    return getattr(self.file, name)

  def close(self):
    self.file.close()
    stato= os.waitpid(self.pid, 0)[1]
    if stato & 0xFF == 0x00:
      stato= stato >> 8
    else:
      stato= stato & 0xFF
    return stato
    
    

def main():
  z= psafepopen(['/usr/bin/figlet'], 'w')
  for i in range(10):
    print i
    z.write(str(i) + "\n")
  z.close()
  z= psafepopen(['/bin/ls'], 'r')
  while 1:
    line= z.readline()
    if not line: break
    sys.stdout.write('> ' + line)
  z.close()
  psafesystem(['figlet', 'system'])

if __name__ == '__main__':
  main()
