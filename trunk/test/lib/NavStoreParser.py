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

import formatter, htmllib, os, string, urllib, re
import Store, NavForm
from TestFailed import TestFailed

newhtmlelements= 'link script frameset style table tr td th tbody' + \
  ' div span'
newhtmlelementsempty= 'frame'

class NavStoreParser(htmllib.HTMLParser):

  def __init__(self, page):
    htmllib.HTMLParser.__init__(self, formatter.NullFormatter())

    # turn on elements that weren't in HTML 2
    for f in newhtmlelements.split():
      self.setifnot('start_' + f, self.fake_start)
      self.setifnot('end_' + f, self.fake_end)
    for f in newhtmlelementsempty.split():
      self.setifnot('do_' + f, self.fake_start)

    self._page= page
    self._httpRoot= page._httpRoot
    self._root= page.root()
    self._ofp= Store.storeopen(page.url(), self._root, 'w')
    self._anchors= {}
    self._forms= {}
    self._frames= {}
    self._siteRoot= page.siteRoot()
    self._url= page.url()
    self.feed(page.body())
    self.close()


  def setifnot(self, att, value):
    if not hasattr(self, att):
      setattr(self, att, value)

  def fake_start(self, attrs): pass

  def fake_end(self): pass

  # parse methods
  def handle_starttag(self, tag, method, attrs):
    attrs= self.fixReferences(attrs)
    self._ofp.write('<' + tag + '\n')
    [self._ofp.write(' %s="%s"' % (a,v)) for (a,v) in attrs
      if a != 'srcreal']
    self._ofp.write('>')
    method(attrs)

  def handle_endtag(self, tag, method):
    self._ofp.write('</%s>' % tag)
    method()

  def handle_data(self, data):
    self._ofp.write(data)
    return htmllib.HTMLParser.handle_data(self, data)

  def start_a(self, attrs):
    hrefs= [h for k,h in attrs if k == 'href']
    if len(hrefs) == 1:
      self._href= hrefs[0]
      self.save_bgn()
    else:
      self._href= None

  def end_a(self):
    if self._href is not None:
      data= self.save_end()
      self._anchors[data]= self._href

  def do_img(self, attrs):
    src= self.getAtt(attrs, 'src')
    srcreal= self.getAtt(attrs, 'srcreal')
    if srcreal is not None:
      uo= urllib.urlopen(srcreal)
      fp= Store.storeopen(srcreal, self._root, 'w')
      fp.write(uo.read())
      uo.close()
      fp.close()

  def do_frame(self, attrs):
    name= self.getAtt(attrs, 'name')
    src= self.getAtt(attrs, 'src')
    srcreal= self.getAtt(attrs, 'srcreal')
    if name is not None:
      t= self._page.testSuite().createSubpage(srcreal)
      self._frames[name]= t

  def start_form(self, attrs):
    name= self.getAtt(attrs, 'name')
    if name is not None:
      action= self.getAtt(attrs, 'action')
      if action is None:
        action= self._url
      method= self.getAtt(attrs, 'method')
      if method is None:
        method= 'get'
      method= method.lower()
      self._currentForm= NavForm.NavForm(name, action, method,
        self._page)

  def end_form(self):
    self._forms[self._currentForm.name()]= self._currentForm

  # form builders

  def do_input(self, attrs):
    name= self.getAtt(attrs, 'name')
    type= self.getAtt(attrs, 'type')
    if type is None:
      type= 'text'
    if name is not None:
      value= self.getAtt(attrs, 'value')
      if type == 'submit':
        self._currentForm.addSubmit(name, value)
      else:
        self._currentForm.addInput(name, value)

  def start_textarea(self, attrs):
    name= self.getAtt(attrs, 'name')
    if name is not None:
      self.save_bgn()
      self._cur_name= name

  def end_textarea(self):
    data= self.save_end()
    self._currentForm.addTextarea(self._cur_name, data)

  def start_select(self, attrs):
    name= self.getAtt(attrs, 'name')
    if name is not None:
      self._currentForm.startSelect(name)

  def end_select(self):
    self._currentForm.endSelect()

  def start_option(self, attrs):
    value= self.getAtt(attrs, 'value')
    selected= self.getAtt(attrs, 'selected')
    self._cur_value= value
    self._cur_selected= selected is not None
    self.save_bgn()

  def end_option(self):
    data= self.save_end()
    self._currentForm.addOption(self._cur_value, self._cur_selected, 
      data)

  # parse utilities

  def getAtt(self, attrs, att):
    atts= [(a,v) for (a,v) in attrs if a == att]
    if len(atts) > 1:
      raise TestFailed('multiple attributes "%s" found: %s' % \
        (att, `atts`))
    if len(atts) == 0:
      return None
    return atts[0][1]


  def fixReferences(self, attrs):
    newattrs= []
    for a,v in attrs:
      if (a == 'href' or a == 'src') and v.find(':') < 0:
        v= self.fixRef(v)
        if a == 'src':
          newattrs.append(('srcreal', v))
          v= Store.storeurl(v, self._root, self._httpRoot)
      newattrs.append((a, v))
    return newattrs

  def fixRef(self, ref):
    if ref.startswith('/'):
      return self._siteRoot + ref[1:]
    else:
      urlparts= self._url.split('/')
      urldir= string.join(urlparts[0:-1], '/')
      return urldir + '/' + ref






  # access parsed information

  def getA(self, contentre):
    return [(d, self._anchors[d]) for d in self._anchors.keys()
      if re.match(contentre, d)]

  def listAs(self):
    return self._anchors

  def getForm(self, formName):
    if not self._forms.has_key(formName):
      raise TestFailed('page does not contain form named %s' %
        formName)
    return self._forms[formName]

  def listForms(self):
    return self._forms

  def getFrame(self, frameName):
    if not self._frames.has_key(frameName):
      raise TestFailed('page does not contain frame named %s' %
        frameName)
    return self._frames[frameName]

  def listFrames(self):
    return self._frames
