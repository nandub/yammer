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
from UserUtilities import *
from KeyStore import *
from InstallSettings import settings


class InternalMarmadukeServer(MdkServlet):
  """Marmaduke servlet for internal user stores"""


  #
  #
  # Service functions
  #
  #


  def generateKey(self, keyid, fullname, email):
    """
    Generates a new key pair and creates a new Yammer account.
    Fails if the account already exists, or if it can not be created.
    In the event of success, returns a struct containing two
    fields, the public and private keys in binary format."""

    self.checkUsername(keyid)
    err= createUser(keyid, email)
    if err is not None:
      self.keyUnavailableFault(keyid)
    return self.generate(keyid, fullname)

  def listDomains(self):
    """
    Returns an array of all domains managed by this Marmaduke
    server."""
    return settings['galeDomains'].split()

  # require auth
  def issue(self, keyid, password):
    """
    For an existing user, returns the key pair as a struct, generating
    it first if it does not exist.  Intended uses: downloading keys
    from a pre-existing account."""
    self.checkPassword(keyid, password)
    try:
      return self.getKeys(keyid)
    except AttributeError:
      return self.reissue(keyid, password)

  # require auth
  def reissue(self, keyid, password):
    """
    For an existing user, creates a new key pair, replacing the old,
    and returns them as a struct.  Intended uses: to replace a key
    that has been compromised, or just to get keys for an existing
    Yammer account."""

    self.checkPassword(keyid, password)
    fullname= getFullname(keyid)
    return self.generate(keyid, fullname)

  # require auth
  def revoke(self, keyid, password):
    """
    Deletes a user and destroys his or her key pair.  After the user
    is destroyed, a new key pair is generated but not returned; this
    ensures that any remaining copies of the key pair are now
    invalid."""

    self.checkPassword(keyid, password)
    deleteUser(keyid)
    self.generate(keyid, '[deleted user]')
    return 'ok'

  def changePassword(self, keyid, password, newpassword):
    """
    Changes a user's Marmaduke/Yammer password."""
    self.checkPassword(keyid, password)
    setPassword(keyid, newpassword)
    return "ok"

  def forgotPassword(self, keyid):
    """
    Resets a user's password and emails the new password to the email
    address on file for that user."""

    try:
      forgotPassword(keyid)
    except 'noEmail':
      raise xmlrpclib.Fault(113, 'Cannot reset password for %s because ' + \
        'user has no email address.' % keyid)
    return "ok"



  #
  #
  # Utility functions
  #
  #

  def checkUsername(self, keyid):
    keyparts= keyid.split('@')
    if len(keyparts) != 2:
      self.keyUnacceptableFault(keyid, 'it is not of the form user@dom.ain')
    if keyparts[1] not in self.listDomains():
      self.keyUnacceptableFault(keyid, 'the domain is not available from ' +
        'this server')
    if not validUsername(keyid):
      self.keyUnacceptableFault(keyid, 'the username is too long, too ' +
        'short, or contains illegal characters')

  def checkPassword(self, keyid, password):
    if checkPassword(keyid, password):
      return
    raise xmlrpclib.Fault(105, 'The password for %s was not correct.' % keyid)

  def keyUnacceptableFault(self, keyid, reason):
    raise xmlrpclib.Fault(110, ('The key %s cannot be issued because %s.' \
      % (keyid, reason)))

  def keyUnavailableFault(self, keyid):
    suggestion= self.getSuggestion(keyid)
    raise xmlrpclib.Fault(111, ('The key %s already exists.  If it is ' + \
      'not yours, try another name.\nSuggestion: %s.') % (keyid, suggestion))

  def generationErrorFault(self, keyid, error):
    raise xmlrpclib.Fault(50, ('Unable to generate key %s.  Error ' + \
      'message: %s.') % (keyid, error))

  def getSuggestion(self, keyid):
    (user, domain)= keyid.split('@')
    for d in [dd for dd in self.listDomains() if dd != domain]:
      t= '%(user)s@%(d)s' % locals()
      if not userExists(t):
        return t
    i= 1
    while 1:
      t= '%(user)s%(i)d@%(domain)s' % locals()
      if not userExists(t):
        return t
      i= i + 1

  def generate(self, keyid, fullname):
    error= gkgen(keyid, fullname, "Marmaduke")
    if error is not None:
      self.generationErrorFault(keyid, error)
    return self.getKeys(keyid)

  def getKeys(self, keyid):
    pr= open(privPath(keyid), 'r')
    prb= xmlrpclib.Binary(pr.read())
    pr.close()
    pu= open(pubPath(keyid), 'r')
    pub= xmlrpclib.Binary(pu.read())
    pu.close()
    return {'private': prb, 'public': pub}

class LdapMarmadukeServer(InternalMarmadukeServer):

  def raiseNotImplemented(self):
    raise xmlrpclib.Fault(99, 'Method not implemented on this server')

  def generateKey(self, keyid, fullname, email):
    """
    This method is not supported in an LDAP environment, because
    in an LDAP environment accounts cannot be created through Yammer
    or Marmaduke, but only through the central LDAP repository."""
    self.raiseNotImplemented()

  def revoke(self, keyid, password):
    """
    Destroys a user's key pair.  In an LDAP managed user store, it
    is not possible to delete a user, but this function makes sure
    that any remaining copies of the old key are invalid."""
    self.checkPassword(keyid, password)
    self.generate(keyid, '[deleted user]')
    return 'ok'

  def changePassword(self, keyid, password, newpassword):
    """
    Not implemented in an LDAP managed user store; passwords
    must be changed through whatever system your LDAP administrators
    have put in place."""
    self.raiseNotImplemented()

  def forgotPassword(self, keyid):
    """
    Not implemented in an LDAP managed user store; passwords
    must be changed through whatever system your LDAP administrators
    have put in place."""
    self.raiseNotImplemented()


if settings['userStore'].startswith('ldap'):
  MarmadukeServer= LdapMarmadukeServer
else:
  MarmadukeServer= InternalMarmadukeServer
