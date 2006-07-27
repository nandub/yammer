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

# we don't want to require this module to exist if you're not using
# ldap, because it doesn't come with python
if settings['userStore'].startswith('ldap'):
  import ldap
  import string
  import sys

  # checks whether the given user can bind with the given password
  # returns None if not, or a hash of user attributes if yes
  def checkPassword(username, password):
    uid= uidForUsername(username)
    ldaps= 0
    if settings['userStore'] == 'ldaps':
      ldaps= 1
    l= ldapBind()
    bindAnonymous(l)
    res= getUserAtts(l, uid)
    dn= res[0][0]
    correct= None
    try:
      if len(password) == 0:
        raise ldap.INVALID_CREDENTIALS, {'desc': 'empty password'}
      l.bind_s(dn, password, ldap.AUTH_SIMPLE)
      res= getUserAtts(l, uid)
      correct= res[0][1]
    except ldap.INVALID_CREDENTIALS, arg:
      sys.stdout.write('invalid credentials for %s: %s\n' %
        (dn, arg[0]['desc']))
      sys.stdout.flush()
    ldapUnbind(l)
    return correct

  def ldapBind():
    ldaps= 0
    if settings['userStore'] == 'ldaps':
      ldaps= 1
      ldap.set_option(ldap.OPT_X_TLS_CACERTFILE,settings['tlsCertFile'])
    l= ldap.initialize(settings['ldapServerURL'])
    if ldaps:
      l.protocol_version=ldap.VERSION3
      l.set_option(ldap.OPT_X_TLS,ldap.OPT_X_TLS_DEMAND)
      l.start_tls_s()
    return l

  def ldapUnbind(l):
    l.unbind_s()

  def getUserAtts(l, uid):
    return l.search_s(settings['userSearchDn'], ldap.SCOPE_SUBTREE,
      '(&(uid=%(uid)s)(objectclass=person))' % locals())

  def uidForUsername(username):
    return username.split('@')[0]

  def bindAnonymous(l):
    l.bind_s('','',ldap.AUTH_SIMPLE)

  def getEmailAndFullName(ua):
    fullname= []
    for a in ['givenname', 'sn']:
      if ua.has_key(a): fullname += ua[a]
    if len(fullname) == 0:
      fullname= '(no name found in ldap)'
    else:
      fullname= string.join(fullname)
    return ua['mail'][0], fullname





# questions for Suth:
#   why do I need the tlsCertFile?
#   are anonymous binds ok?  Do we get extra information if
#   authenticated?


