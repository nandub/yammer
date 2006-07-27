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


import threading, YammerUtils

class YammerLock(threading._RLock):

  def __init__(self):
    threading._RLock.__init__(self)

  def acquire(self, blocking=1):
    YammerUtils.debugMessage("acquiring lock %s..." % self)
    threading._RLock.acquire(self, blocking)
    YammerUtils.debugMessage("acquired lock %s..." % self)

  def release(self):
    threading._RLock.release(self)
    YammerUtils.debugMessage("released lock %s..." % self)


