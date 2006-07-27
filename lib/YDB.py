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


import MySQLdb, string, sys, YammerUtils
from InstallSettings import settings
from types import *

m_cursor= None


def getCursor():
  global m_cursor
  dbconn= MySQLdb.connect(host= settings['dbHost'],
                          user= settings['dbUser'],
                          passwd= settings['dbPassword'],
                          db= settings['dbSchema'])
  m_cursor= dbconn.cursor()
  return m_cursor

def close(cursor):
  if hasattr(cursor, 'connection'):
    cursor.connection.close()
  else:
    cursor.close()

#
# executes a query with variables interpolated from a hash;
# the hash values are passed through a sql-quoting filter
#

def executeQuery(curs, query, quotehash):


  def utf8armor(x):
    if isinstance(x, unicode):
      return x.encode('utf8')
    elif isinstance(x, (list, tuple, dict)):
      return ''
    else:
      return x

  def reunicodify(row):
    newrow= []
    for col in row:
      if isinstance(col, str):
        col= col.decode('utf8')
      newrow.append(col)
    return newrow


  newhash= {}
  for key in quotehash.keys():
    newhash[key]= utf8armor(quotehash[key])
  if settings.has_key('debugSQL'):
    YammerUtils.debugMessage('executing query: %s\n\nnewhash: %s' %
        (query, `newhash`))
  curs.execute(query, newhash)
  return [reunicodify(row) for row in curs.fetchall()]


