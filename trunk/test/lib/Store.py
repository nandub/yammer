# 
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

import os, string

def storeopen(url, root, mode):
  path= storepath(url, root)
  return open(path, mode)

def storepath(url, root):
  _path= root + '/' + url.replace('://', '_')
  if _path.endswith('/'):
    _path += 'index.psp'
  try:
    os.makedirs(os.path.dirname(_path))
  except OSError, args:
    if args.errno != 17:
      raise OSError, args
  if _path.endswith('.psp'):
    _path += '.html'
  return _path

def storeurl(url, root, httproot):
  path= storepath(url, root)
  rootparts= root.split('/')
  realroot= string.join(rootparts[0:-1], '/')
  return httproot + path[len(realroot)+1:]
