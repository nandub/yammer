#!/usr/bin/env python

import sys
import os, os.path
if not os.environ.has_key('ENV_HARNESS'):
  envh= os.path.dirname(sys.argv[0]) + '/envharness'
  os.execv(envh, [envh] + sys.argv)

import threading, time, YDB

def getQuery(map, query):
  curs= YDB.getCursor()
  results= YDB.executeQuery(curs, query, map)
  YDB.close(curs)
  return results

class QueryThread(threading.Thread):
  def run(self):
    while 1:
      time.sleep(2)
      results= getQuery({}, '''
        SELECT pkey, pvalue
        FROM userprefs_t
        WHERE login = 'jtr@dev.yammer.net'
        ''')

threads= int(sys.argv[1])
for i in range(threads):
  t= QueryThread()
  t.start()
