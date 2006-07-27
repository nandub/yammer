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


import YDB, md5, sys, smtplib, random, re, string, UserPrefs, KeyStore
import os
from YammerException import YammerException
import LDAPUtilities
from InstallSettings import settings
if settings['userStore'].startswith('ldap'):
  import ldap

def ldapUidForUsername(username):
  return username.split('@')[0]

def checkPassword(username, password):
  if validUsername(username):
    if settings['userStore'].startswith('ldap'):
      return LDAPUtilities.checkPassword(username, password)
    else:
      curs= YDB.getCursor()
      num= curs.execute(('SELECT password FROM user_t WHERE ' + \
                      'login="%s"') % (username))
      results= curs.fetchone()
      YDB.close(curs)
      if results:
        correctpassword= results[0]
        return correctpassword == hashPassword(password)
  return 0

def makeSureNotLdap():
  if settings['userStore'].startswith('ldap'):
    raise YammerException, \
      'this operation is not supported with the %s userStore' % \
      settings['userStore']

def validUsername(username):
  us= username.split('@')
  if len(us) != 2:
    return 0
  u,d= us
  if d not in settings['galeDomains'].split():
    return 0
  return re.match("^\w{1,64}$", u)

def setPassword(username, password):
  makeSureNotLdap()
  hashedpassword= hashPassword(password)
  curs= YDB.getCursor()
  curs.execute(('SELECT * FROM user_t WHERE ' + \
                  'login="%s"') % (username))
  if curs.fetchone():
    curs.execute(('UPDATE user_t SET password="%s" WHERE ' + \
                    'login = "%s"') % 
                    (hashedpassword, username))
  else:
    curs.execute(('INSERT INTO user_t VALUES ' + \
                    '("%s", "%s")') %
                   (username, hashedpassword))
    YDB.close(curs)




def hashPassword(password):
  import md5
  digest= md5.new(password).digest()
  hexdigest= ''
  for c in digest:
    hexdigest= hexdigest + ('%02x' % (ord(c)))
  return hexdigest

def sendUserPasswordEmail(username, password, subject):
  makeSureNotLdap()
  frome= settings['maintEmail']
  u= UserPrefs.getInstance(username)
  email= u['email.address']
  subject='%s for %s on %s' % (subject, username, settings['siteName'])
  message= """Your new password is '%s'.""" % (password)
  sendEmail(frome, email, subject, message)

def sendEmail(frome, to, subject, body):
  makeSureNotLdap()
  try:
    server= smtplib.SMTP(settings['smtpServer'])
    message= 'From: %(frome)s\nTo: %(to)s\nSubject: %(subject)s\n\n' % \
      locals() + body
    server.sendmail(frome, to, message)
    server.quit()
  except:
    value= sys.exc_value
    type= sys.exc_type
    try:
      server.quit()
    except:
      pass
    return "Unable to send email: %s %s." % (type, value)
  return None

def randomPassword():
  passwordChars= string.letters + string.digits + '/!+-%#'
  password= ''
  for i in range(16):
    password= password + \
      passwordChars[random.randint(0, len(passwordChars) - 1)]
  return password

def createUser(username, email):
  makeSureNotLdap()
  if not validUsername(username):
    return 'Username must be less than 64 characters and must ' + \
      'consist of letters, numbers, and/or underscores.'
  else:
    if userExists(username):
      return 'User already exists; please pick a new name.'
    else:
      password= randomPassword()
      setPassword(username, password)
      u= UserPrefs.getInstance(username)
      u['email.address']= email
      err= sendUserPasswordEmail(username, password,
        'new account password')
      return err

def userExists(username):
  curs= YDB.getCursor()
  results= YDB.executeQuery(curs,
    'SELECT login FROM user_t WHERE login=%(username)s',
    locals())
  YDB.close(curs)
  return results is not None and len(results) > 0

def deleteUser(user):
  makeSureNotLdap()
  curs= YDB.getCursor()
  YDB.executeQuery(curs, 'DELETE FROM user_t ' +
    'WHERE login = %(user)s', locals())
  YDB.executeQuery(curs, 'DELETE FROM userprefs_t ' +
    'WHERE login = %(user)s', locals())
  galeid= user
  path= KeyStore.privPath(galeid)
  if path is not None:
    os.unlink(path)
  YDB.close(curs)

def forgotPassword(username):
  makeSureNotLdap()
  u= UserPrefs.getInstance(username)
  e= u['email.address']
  if e is not None and e.find('@') > 0:
    password= randomPassword()
    setPassword(username, password)
    return sendUserPasswordEmail(username, password, 'reset password')
  else:
    raise 'noEmail'
