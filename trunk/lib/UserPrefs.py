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

import threading

from InstallSettings import settings
import YDB, sys, MySQLdb
import YammerLock


prefCache= {}

defaultprefs= {

  'email.address':
  ['Email address // used only for authentication',
   ''],

  'do.autorefresh':
  ['Do periodic refresh of log pane? // if unset, ' +
   'hit resubscribe button for new messages',
   'yes'],

  'subs.quick':
  ['List of useful subscriptions // colon separated',
   settings['subsQuick']],

  'send.geometry':
  ['Size of send box // may be of form ROWS or COLUMNSxROWS',
   '5'],

  'logpager.puffcount':
  ['Number of puffs to show in log window',
   '10'],

  'stylesheet':
  ['Look and feel',
   'gray'],

  'gale.sender':
  ['Full name to embed in messages // ' +
   'leave empty to use the name stored in the key',
   ''],

  'front.page':
  ['Gale client interface',
   '/gale/logbased/frameset.psp'],

  'thumbnail.shrink':
  ['Thumbnail display',
   'half-size'],

  'compact.display':
  ['Compact message display',
   'yes'],

  'resub.bar':
  ['Resubscribe bar position',
   'both'],

  'killfile.contents':
  ['Users, locations, and keywords not to show',
   ''],

  'killfile.on':
  ['Use killfile',
   'yes'],

  'autologin.hash':
  ['(hidden) Value cookie must have to authenticate autologin',
   ''],

  'last.private.time':
  ['(hidden) time that last private message was confirmed seen',
   ''],

  'last.activity':
  ['(hidden) last activity timestamp',
   '']
}


def getInstance(user):
  global prefCache
  if not prefCache.has_key(user):
    prefCache[user]= UserPrefs(user)
  return prefCache[user]

def getDefault(pkey):
  global defaultprefs
  return defaultprefs[pkey][1]





class UserPrefs:

  def __init__(self, username, transaction=None):
    self.username= username
    self.transaction= transaction
    self.lock= YammerLock.YammerLock()

    # create self.prefs from the database
    self.refresh()




  # Um, but...
  def getQuery(self, map, query):
    curs= YDB.getCursor()
    results= YDB.executeQuery(curs, query, map)
    YDB.close(curs)
    return results


  def getDisplay(self, pkey):
    global defaultprefs
    return defaultprefs[pkey][0]

  def isBoolean(self, pkey):
    default= getDefault(pkey)
    return default in ['yes', 'no']

  def refresh(self):
    username= self.username
    results= self.getQuery(locals(), '''
      SELECT pkey, pvalue
      FROM userprefs_t
      WHERE login = %(username)s
      ''')
    self.prefs= {}
    for res in results:
      (pkey, pvalue)= res
      self.prefs[pkey]= pvalue

  def has_key(self, key):
    global defaultprefs
    return defaultprefs.has_key(key)


  def keys(self):
    global defaultprefs
    return defaultprefs.keys()

  def __setitem__(self, pkey, pvalue):
    self.lock.acquire()
    try:
      updatesql= '''
        UPDATE userprefs_t
        SET pvalue=%(pvalue)s
        WHERE login=%(username)s AND pkey=%(pkey)s
        '''
      insertsql= '''
        INSERT INTO userprefs_t 
        (login, pkey, pvalue)
        VALUES (%(username)s, %(pkey)s, %(pvalue)s)
        '''
      if self.prefs.has_key(pkey):
        sql= updatesql
      else:
        sql= insertsql
      self.prefs[pkey]= pvalue
      username= self.username
      try:
        self.getQuery(locals(), sql)
      except MySQLdb.IntegrityError, sqlcode:
        #print 'sql exception %d, %s' % sqlcode.args
        #sys.stdout.flush()
        if sqlcode.args[0] == 1062:
          self.getQuery(locals(), updatesql)
    finally:
      self.lock.release()

  def getPrefLimit(self, pkey, low, high):
    value= self[pkey]
    if value:
      value= int(value)
      if value < low:
        return low
      elif value > high:
        return high
    return value


  def eraseSessionPref(self, pkey):
    pass

  def deleteSessionPrefs(self):
    pass

  def __getitem__(self, pkey):
    if self.prefs.has_key(pkey):
      return self.prefs[pkey]
    else:
      global defaultprefs
      if defaultprefs.has_key(pkey):
        default= defaultprefs[pkey][1]
        self[pkey]= default
        return default
      return None




# wraps a UserPrefs object and adds lookup of session-temporary
# preferences
class SessionUserPrefs(UserPrefs):

  def __init__(self, userPrefs, transaction):
    self.__dict__['userPrefs']= userPrefs
    self.__dict__['transaction']= transaction

  def __getattr__(self, attr):
    return getattr(self.userPrefs, attr)

  def __setattr__(self, attr, v):
    return setattr(self.userPrefs, attr, v)

  def setSessionPref(self, pkey, pvalue):
    # should throw an exception if no session, because this should
    # never be called in that case
    session= self.transaction.session()
    session.setValue('pref.' + pkey, pvalue)

  def eraseSessionPref(self, pkey):
    if self.hasUsableSession():
      session= self.transaction.session()
      if session.hasValue('pref.' + pkey):
        session.delValue('pref.' + pkey)

  def deleteSessionPrefs(self):
    if self.hasUsableSession():
      session= self.transaction.session()
      values= session.values()
      [session.delValue(x) for x in values if x.startswith('pref.')]

  def __getitem__(self, pkey):
    if self.hasUsableSession():
      session= self.transaction.session()
      if session.hasValue('pref.' + pkey):
        return session.value('pref.' + pkey)
    return self.userPrefs[pkey]

  def hasUsableSession(self):
    if self.transaction is not None:
      if hasattr(self.transaction, '_session'):
        return self.transaction.hasSession()
      else:
        self.transaction= None
    return None
