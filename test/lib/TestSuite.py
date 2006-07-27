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

import TestPage, Store, TestFailed
from types import *


class TestSuite:

  def __init__(self, root, httproot):
    self._root= root
    self._httproot= httproot
    self._id= 0
    self._cookies= {}
    self.writeFrameset()
    self.startNav()

  def writeFrameset(self):
    frameset= open(self._root + 'index.html', 'w')
    frameset.write("""
      <html>
        <head><title>Test run</title></head>
        <frameset cols="200,*">
          <frame src="nav.html" scrolling="yes" name="suite">
          <frame src="about:blank" scrolling="yes" name="case">
        </frameset>
      </html>
      """)
    frameset.close()

  def startNav(self):
    self._navFrame= open(self._root + 'nav.html', 'w')
    self._navFrame.write("""
      <html>
        <body>
      """)

  def finish(self):
    self._navFrame.write("""
        </body>
      </html>""")
    self._navFrame.close()

  def createPage(self, pagetests, url, postargs=None, forceget=0):
    self._id += 1
    id= self._id
    t= self.createSubpage(url, postargs, forceget)
    testpage= Store.storeurl(t.url(), self._root + str(self._id),
      self._httproot)
    self._navFrame.write("""
      <a target="case" href="%(testpage)s">Test: %(id)s</a>
      <ul>
      """ % locals())
    if pagetests.__doc__ is not None:
      lines= pagetests.__doc__.split('\n')
      for line in lines:
        self._navFrame.write("""
          <li>%(line)s""" % locals())
    self._navFrame.write("</ul>")
    try:
      next= pagetests(t)
      self._navFrame.write("<b>passed</b><hr>\n")
      return next
    except TestFailed.TestFailed, args:
      msg= args[0]
      self._navFrame.write("<b>FAILED</b>: %(msg)s<hr>\n" % locals())
      return None

  def createSubpage(self, url, postargs=None, forceget=0):
    print
    print 'subpage'
    root= self._root + str(self._id)
    t= TestPage.TestPage(self, root, self._httproot, url, self._cookies,
      postargs, forceget)
    return t

  def setCookies(self, cookies):
    self._cookies= cookies
    print "setting cookies to " + `self._cookies`

  def runTests(self):
    next= self.initialUrl()
    testfunctions= self.testFunctions()
    for testfunc in testfunctions:
      if type(next) is InstanceType:
        next= next.submit(testfunc)
      else:
        next= self.createPage(testfunc, next)
      if next is None:
        break
    self.finish()


