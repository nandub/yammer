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


import MySQLdb, string, sys, YDB, YammerUtils
from types import *
from InstallSettings import settings
from pygale import pygale
from YDB import executeQuery
import Gale


#
# puff format:
# a hash containing the following keys
#   body: text of the body
#   sender: name of sender key
#   from: friendly name of sender
#   date: sent date
#   ssdate: server-side date (not used?)
#   locations: array of locations
#   keywords: array of keywords (0-length array if none)
#   encrypted: flag indicating message was encrypted
#



def locWhereClause(subs):

  def get1WhereClause(sub):
    if sub[0] == '/':
      return "t.cat = '%s' OR t.cat LIKE '%s.%%%%'" % (sub[1:], sub[1:])
    else:
      subparts= sub.split('@')
      if len(subparts) > 1:
        return "t.cat = '%s' OR t.cat LIKE '%s.%%%%@%s'" % \
          (sub, subparts[0], subparts[1])
    return "t.cat LIKE '%s@%%%%' OR t.cat LIKE '%s.%%%%@%%%%'" % (sub, sub)

  return string.join(map(get1WhereClause, subs), ' OR ')

def userWhereClause(users):

  def get1WhereClause(user):
    return "p.sender = '%s'" % user

  return string.join(map(get1WhereClause, users), ' OR ')

def interleave(rs1, rs2, limit, num):
  i1, i2, returnset= (0, 0, [])
  for j in xrange(num):
    if i1 < len(rs1) and \
      ((i2 < len(rs2) and rs1[i1][0] > rs2[i2][0]) or \
       i2 >= len(rs2)):
      returnset.append(rs1[i1])
      i1= i1 + 1
    elif i2 < len(rs2) and \
      ((i1 < len(rs1) and rs1[i1][0] <= rs2[i2][0]) or \
       i1 >= len(rs1)):
      returnset.append(rs2[i2])
      if (i1 < len(rs1) and rs1[i1][0] == rs2[i2][0]):
        i1= i1 + 1
      i2= i2 + 1
    else:
      break
  return returnset

#
# fetches a batch of puffs matching a subscription
#

def getPuffs(whereclauses, orderclause, limitclause):
  if orderclause is None:
    orderclause= 'GROUP BY p.puffid DESC'
  whereclauses += ['NOT (%s)' % locWhereClause(['_gale'])]
  query1= 'SELECT p.puffid ' + \
          'FROM puffs_t p, tos_t t ' + \
          'WHERE (' + \
          string.join(['(%s)' % c for c in whereclauses], ' AND ') + \
          ') AND t.puffid=p.puffid ' + \
          orderclause + ' ' + limitclause
  curs= YDB.getCursor()
  resultset= executeQuery(curs, query1, {})
  YDB.close(curs)
  return buildPuffList(resultset)

def fetchPuffs(subs, private, limit, num, killfile=[]):

  resultset1, whereclause= [], None
  if len(subs) > 0 or private is not None:
    expandedSubs= map(pygale.expand_aliases, subs)
    subs= []
    for sub in expandedSubs:
      canon, members= pygale.lookup_location(sub)
      if members is not None and len(members) == 1 and \
          members[0] == '':
        subs.append(sub)
    if private is not None:
      subs.append(private)
    if len(subs) > 0:
      whereclause= locWhereClause(subs)
  lockills= [kfe[1] for kfe in killfile if kfe[0] == 'loc']
  clauses= [whereclause]
  if len(lockills) > 0:
    YammerUtils.debugMessage(`clauses`)
    sys.stdout.flush()
    clauses += ['NOT (%s)' % locWhereClause(lockills)]
  userkills= [kfe[1] for kfe in killfile if kfe[0] == 'user']
  if len(userkills) > 0:
    clauses += ['NOT (%s)' % userWhereClause(userkills)]
  return getPuffs(clauses, None,
    'LIMIT %(limit)s, %(num)s' % locals())




# takes as input a result set whose first column is puffid
def buildPuffList(resultset):

  query1s= 'SELECT puffid, body, sender, `from`, ' + \
           'date, ssdate, encrypted ' + \
           'FROM puffs_t WHERE ' + \
           'puffid in (%(puffids)s) ORDER BY puffid DESC'

  curs= YDB.getCursor()
  if len(resultset) > 0:
    puffids= string.join([str(x[0]) for x in resultset], ",")
    resultset= executeQuery(curs, query1s % locals(), locals())
    query2= 'SELECT puffid, cat, islocation ' + \
            'FROM tos_t WHERE puffid in ' + \
            '(' + puffids + ') ORDER BY puffid'
    resultset2= executeQuery(curs, query2, locals())
  else:
    resultset2= []
  YDB.close(curs)
  returnset= []
  for row in resultset:
    i,b,s,f,d,ss,e= row
    if e:
      b= Gale.deobscureString(b)
    curhash= {'body': b, 'sender': s, 'from': f, 
              'date': d, 'locations': [], 'keywords': [],
              'puffid': i, 'ssdate': ss, 'encrypted': e}
    for lockwd in [x for x in resultset2 if x[0] == i]:
      id,cat,isloc= lockwd
      if isloc:
        curhash['locations'].append(cat)
      else:
        curhash['keywords'].append(cat)
    returnset.append(curhash)
  return returnset



# 
# adds a puff to the database; this involves one row added
# to puffs_t and one row for each location and column added
# to tos_t
# 

def insertPuff(puff):
  pufftinsert= 'INSERT INTO puffs_t ' + \
          '( `body`,   `sender`,   `from`,   `date`,    ' + \
          ' `ssdate`,   `encrypted`) ' + \
    'VALUES(%(body)s, %(sender)s, %(from)s, %(date)s, ' + \
          '%(ssdate)s, %(encrypted)s) '
  tostinsert= 'INSERT INTO tos_t ' + \
    'VALUES(%(puffid)s, %(cat)s, %(islocation)s)'

  curs= YDB.getCursor()
  executeQuery(curs, pufftinsert, puff)
  puffid= curs.lastrowid
  islocation= 1
  for cat in puff['locations']:
    executeQuery(curs, tostinsert, locals())
  islocation= 0
  for cat in puff['keywords']:
    executeQuery(curs, tostinsert, locals())
  YDB.close(curs)




