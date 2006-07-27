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


from WebKit.XMLRPCServlet import XMLRPCServlet
from xmlrpclib import xmlrpclib
from InstallSettings import settings

# base Heathcliff (remote gale log access protocol) servlet
class HcfServlet(XMLRPCServlet):
  """
  Fault codes:
    1    internal error
    99   method not implemented
    
  The 100-series fault codes represent user-level errors, and the
  corresponding fault strings are suitable to be displayed to a user.
  Fault codes lower than 100 represent server-side errors and the
  fault strings contain information that would be useful in a bug
  report.

  Some servers may not support some methods.  An attempt to call an
  unsupported method will result in fault code 99.
  """

  def respondToPost(self, transaction):
    self._transaction= transaction
    return XMLRPCServlet.respondToPost(self, transaction)

  def call(self, methodName, *args, **keywords):
    #self.guard()
    return XMLRPCServlet.call(self, methodName, *args, **keywords)

  def exposedMethods(self):
    return ['generateKey', 'listDomains', 'issue', 'reissue',
      'revoke', 'changePassword', 'forgotPassword']
  
  # (a) arbitrary order
  # (b) temporal order
  #     chron - Chronological order (oldest first)
  #     inverchron - Inverse of said (latest first)
  # 

  def generateKey(self, keyid, fullname, email):
    pass

  def listDomains(self):
    pass

  # require auth
  def issue(self, keyid, password):
    pass

  # require auth
  def reissue(self, keyid, password):
    pass

  # require auth
  def revoke(self, keyid, password):
    pass

  def changePassword(self, keyid, password, newpassword):
    pass

  def forgotPassword(self, keyid):
    pass

  def guard(self):
    if not self.isSSLed():
      env= self._transaction.request().environ()
      host= env['SERVER_NAME']
      port= settings['httpdSSLServerPort']
      path= env['REQUEST_URI']
      raise xmlrpclib.Fault(100, 'only SSL access allowed; try ' + \
        'https://%(host)s:%(port)s%(path)s' % locals())
        

  def isSSLed(self):
    env= self._transaction.request().environ()
    return env is not None and env.has_key('HTTPS') and env['HTTPS'] == 'on'
