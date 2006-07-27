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


from xmlrpclib import xmlrpclib
from MdkServlet import MdkServlet

class MarmadukeServerMockup(MdkServlet):

  def generateKey(self, keyid, fullname, email):
    self.guard()
    return {'private': xmlrpclib.Binary("aouesaotusnth"),
            'public': xmlrpclib.Binary("aountoaunueo")}

  def listDomains(self):
    self.guard()
    return ['yammer.net', 'hexonxonx.net']

  # require auth
  def reissue(self, keyid, password):
    self.guard()
    return self.generateKey(keyid, 'whoopsy', 'blah@blah')

  # require auth
  def revoke(self, keyid, password):
    self.guard()
    return "ok"

  def changePassword(self, keyid, password, newpassword):
    return "ok"

  def forgotPassword(self, keyid):
    return "ok"
