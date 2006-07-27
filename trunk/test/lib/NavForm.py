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

from TestFailed import TestFailed

INPUT_TYPE= 'input'
TEXTAREA_TYPE= 'textarea'
SELECT_TYPE= 'select'
SUBMIT_TYPE= 'submit'


class NavForm:
  def __init__(self, name, action, method, page):
    self._name= name
    self._page= page
    self._action= action
    self._method= method
    self._children= {}

  # build methods
  def addInput(self, name, value=None):
    self._children[name]= {'type': INPUT_TYPE, 'value': value}

  def addSubmit(self, name, value=None):
    self._children[name]= {'type': SUBMIT_TYPE, 'value': value}

  def addTextarea(self, name, value=None):
    self._children[name]= {'type': TEXTAREA_TYPE, 'value': value}

  def startSelect(self, name):
    self._currentSelect= {'type': SELECT_TYPE, 'name': name, 'options': []}

  def addOption(self, value, selected=0, display=None):
    if display is None:
      display= value
    if selected:
      self._currentSelect['value']= value
    self._currentSelect['options'].append((display, value))

  def endSelect(self):
    if self._currentSelect is not None:
      self._children[self._currentSelect['name']]= self._currentSelect
    self._currentSelect= None

  def assertType(self, item, type):
    if item['type'] != type:
      raise TestFailed('type of form child %s was not %s but rather %s' \
        (name, type, item['type']))

  def postArgs(self):
    args= {}
    for child in self._children.keys():
      arg= self._children[child]['value']
      if arg is None:
        arg= ''
      args[child]= arg
    return args

  # manipulators (use after built)
  def setField(self, name, value):
    self._children[name]['value']= value

  def listOptions(self, name):
    item= self._children[name]
    self.assertType(item, SELECT_TYPE)
    return item['options']

  def setSubmitName(self, name):
    item= self._children[name]
    self.assertType(item, SUBMIT_TYPE)
    self._submitName= name

  def submit(self, testfunc):
    print "submitting form " + self.name()
    return self._page.testSuite().createPage(testfunc, self._action,
      self.postArgs(), self._method == 'get')


  # return name of form
  def name(self):
    return self._name
