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

import urllib, urllib2
import string
import NavStoreParser
from TestFailed import TestFailed


class TestPage:

  #
  # root: directory root for this particular test; used for storage
  # url: url of page
  # cookies: hash of cookie strings, ex. {'_SID_': '120', 'autologin': '1'}
  # postargs: hash of post arguments
  # forceget: use postargs as GET args
  #
  def __init__(self, testsuite, root, httpRoot, url, cookies,
      postargs= None, forceget=0):
    self._testsuite= testsuite
    self._root= root
    self._httpRoot= httpRoot
    self._sourceURL= url
    params= None
    if postargs is not None:
      if forceget:
        url= url + '?' + params
      else:
        params= urllib.urlencode(postargs)
    r= urllib2.Request(url, params)
    if cookies is not None:
      r.add_header('Cookie', string.join(
        ['%s=%s' % (k, cookies[k]) for k in cookies.keys()], '; '))
    urlObj= urllib2.urlopen(r)
    self._url= urlObj.geturl()
    self._body= urlObj.read()
    self._info= urlObj.info()
    if cookies is None:
      cookies= {}
    self._cookies= cookies.copy()
    for c in self._info.headers:
      if c.startswith('Set-Cookie'):
        cook= c.split(': ', 1)[1].split(';')[0]
        cook.strip()
        k,v= cook.split('=', 1)
        self._cookies[k]= v
    self._testsuite.setCookies(self._cookies)
    self.parse()
    print 'went to: ' + self.url()
    print 'cookies: ' + `self.cookies()`
    print 'forms: %s' % self.listForms()
    print 'frames: %s' % self.listFrames()
    print 'anchors: %s' % self.listAs()
    print


  def parse(self):
    self._parser= NavStoreParser.NavStoreParser(self)

  # accessors 

  def cookies(self):
    return self._cookies

  def url(self):
    return self._url

  def body(self):
    return self._body

  def info(self):
    return self._info

  def root(self):
    return self._root

  def testSuite(self):
    return self._testsuite

  def siteRoot(self):
    urlparts= self.url().split('/')
    return string.join(urlparts[0:3], '/') + '/'



  # parsed content

  def getA(self, contentre):
    return self._parser.getA(contentre)

  def listAs(self):
    return self._parser.listAs()

  def getForm(self, formName):
    return self._parser.getForm(formName)

  def listForms(self):
    return self._parser.listForms()

  def getFrame(self, frameName):
    return self._parser.getFrame(frameName)

  def listFrames(self):
    return self._parser.listFrames()
