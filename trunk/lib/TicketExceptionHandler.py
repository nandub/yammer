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


from WebKit.ExceptionHandler import ExceptionHandler, htTitle, singleton
from WebUtils.Funcs import urlEncode, htmlForDict
from WebUtils.HTMLForException import HTMLForException
import YammerUtils, traceback, string, os.path, sys
from types import DictType
from InstallSettings import settings

class TicketExceptionHandler(ExceptionHandler):

  def __init__(self, application, transaction, excInfo):
    ExceptionHandler.__init__(self, application, transaction, excInfo)

  def getGaleId(self):
    trans= self._tra
    if trans.hasSession():
      session= trans.session()
      if session.hasValue('username'):
        username= session.value('username')
        return username
    return None

  def publicErrorPage(self):
    html= '''<html>
  <head>
    <title>Error</title>
  </head>
  <body fgcolor=black bgcolor=white>
    %s
    <p> %s
''' % (htTitle('Error'), self.setting('UserErrorMessage'))
    debugInfo= self.generateDebugInfo()
    html += debugInfo[0]
    html += '</body></html>'
    return html

  def privateErrorPage(self):
    ''' Returns an HTML page intended for the developer with useful information such as the traceback. '''
    html = ['''
<html>
  <head>
    <title>Error</title>
  </head>
  <body fgcolor=black bgcolor=white>
%s
<p> %s''' % (htTitle('Error'), self.setting('UserErrorMessage'))]

    html.append(self.htmlDebugInfo())

    html.append('</body></html>')
    return string.join(html, '')

  def htmlDebugInfo(self):
    return string.join(self.generateDebugInfo(), '<hr>')

  def generateDebugInfo(self):
    ''' Return HTML-formatted debugging information about the current exception. '''
    self.html= []
    self.bugdesc= "(please click *Edit* and enter a brief description of " + \
      "what you were doing, here)\n\n====\n"
    self.reporttitle= 'unexpected error'
    self.writeHTML()
    html= ''.join(self.html)
    self.html= None
    contact= self.getGaleId()
    if contact:
      contact= 'gale ' + contact
    else:
      contact= ''
    version= YammerUtils.getVersionString()
    desc= self.bugdesc.replace('"', '&quot;')
    title= self.reporttitle
    return ("""<form method="post" action="http://cvstrac.ofb.net/tktnew">
      <input type="hidden" name="t" value="%(title)s">
      <input type="hidden" name="w" value="jtr">
      <input type="hidden" name="c" value="%(contact)s">
      <input type="hidden" name="s" value="yammer.net">
      <input type="hidden" name="v" value="%(version)s">
      <input type="hidden" name="y" value="event">
      <input type="hidden" name="r" value="3">
      <input type="hidden" name="p" value="3">
      <input type="hidden" name="d" value="%(desc)s">
      You can file an incident report about this error.  If you file
      an incident report, relevant information about the problem will
      be saved in the bug database and you will be given a chance to
      type in extra information, such as a description of what you
      were doing.  Filling out an incident report is very helpful and
      makes it much more likely that the developer will be able to fix
      the problem.  If you would like to file an incident report,
      please click here:<p>
      <input type="submit" name="submit" value="submit incident report">
      """ % locals(), html)


  def htmlWrite(self, s):
    ExceptionHandler.write(self, s)

  def descWrite(self, s):
    self.bugdesc += str(s)

  def write(self, s):
    self.htmlWrite(s)
    self.descWrite(s)

  def htmlWriteln(self, s):
    ExceptionHandler.writeln(self, s)

  def descWriteln(self, s):
    self.bugdesc += str(s) + '\n\n'

  def writeln(self, s):
    self.htmlWriteln(s)
    self.descWriteln(s)


  def writeDict(self, d):
    self.htmlWriteln(htmlForDict(d, filterValueCallBack=self.filterDictValue,
      maxValueLength=self._maxValueLength))
    keys= d.keys()
    keys.sort()
    for key in keys:
      self.descWrite(self.descRepr(key) + ':')
      values= string.split(str(d[key]), '\n')
      self.descWriteln(values[0])
      for value in values[1:]:
        self.descWriteln('      ' + self.descRepr(value))


  def htmlWriteTable(self, listOfDicts, keys=None):
    """
    Writes a table whose contents are given by listOfDicts. The
    keys of each dictionary are expected to be the same. If the
    keys arg is None, the headings are taken in alphabetical order
    from the first dictionary. If listOfDicts is "false", nothing
    happens.

    The keys and values are already considered to be HTML.

    Caveat: There's no way to influence the formatting or to use
    column titles that are different than the keys.

    Note: Used by writeAttrs().
    """
    if not listOfDicts:
      return

    if keys is None:
      keys = listOfDicts[0].keys()
      keys.sort()

    wr = self.htmlWriteln
    wr('<table>\n<tr>')
    for key in keys:
      wr('<td bgcolor=#F0F0F0><b>%s</b></td>' % key)
    wr('</tr>\n')

    for row in listOfDicts:
      wr('<tr>')
      for key in keys:
        wr('<td bgcolor=#F0F0F0>%s</td>' % self.filterTableValue(row[key], key, row, listOfDicts))
      wr('</tr>\n')

    wr('</table>')


  def descWriteTable(self, listOfDicts, keys=None):
    if not listOfDicts: return

    if keys is None:
      keys= listOfDicts[0].keys()
      keys.sort()

    wrp= self.descWrite
    wr= self.descWriteln

    wr('keys: ' + string.join(keys, ' '))
    for row in listOfDicts:
      for key in keys:
        wrp('{%s} ' % self.filterTableValue(row[key], key, row,
          listOfDicts))
      wr('')

  def writeTable(self, listOfDicts, keys=None):
    self.htmlWriteTable(listOfDicts, keys)
    self.descWriteTable(listOfDicts, keys)

  def htmlWriteTraceback(self):
    self.htmlWriteTitle('Traceback')
    self.htmlWrite('<p> <i>%s</i>' % self.servletPathname())
    self.htmlWrite(HTMLForException(self._exc))

  def htmlWriteTitle(self, s):
    self.htmlWriteln(htTitle(s))

  def writeTitle(self, s):
    self.htmlWriteTitle(s)
    self.descWriteln('\n\n====\n\n' + s)

  def writeAttrs2(self, obj, attrNames, reprfunc, wrTableFunc):
    """
    Writes the attributes of the object as given by attrNames.
    Tries obj._name first, followed by obj.name(). Is resilient
    regarding exceptions so as not to spoil the exception report.
    """
    rows = []
    for name in attrNames:
      value = getattr(obj, '_'+name, singleton) # go for data attribute
      try:
        if value is singleton:
          value = getattr(obj, name, singleton) # go for method
          if value is singleton:
            value = '(could not find attribute or method)'
          else:
            try:
              if callable(value):
                value = value()
            except Exception, e:
              value = '(exception during method call: %s: %s)' % (e.__class__.__name__, e)
            value = reprfunc(value)
        else:
          value = reprfunc(value)
      except Exception, e:
        value = '(exception during value processing: %s: %s)' % (e.__class__.__name__, e)
      rows.append({'attr': name, 'value': value})
    wrTableFunc(rows, ('attr', 'value'))

  def writeAttrs(self, obj, attrNames):
    self.writeAttrs2(obj, attrNames, self.repr, self.htmlWriteTable)
    self.writeAttrs2(obj, attrNames, self.descRepr, self.descWriteTable)

  def descRepr(self, x):
    if type(x) is DictType:
      reps= []
      for k in x.keys():
        reps.append(self.descRepr(k) + ': ' + self.descRepr(x[k]))
      return '{' + string.join(reps, ', ') + '}'
    else:
      rep = repr(x)
      if self._maxValueLength and len(rep) > self._maxValueLength:
        rep = rep[:self._maxValueLength] + '...'
      if rep.find('_') >= 0 or rep.find('*') >= 0:
        rep= '{quote: ' + rep + '}'
      return rep

  def writeTraceback(self):
    self.htmlWriteTraceback()
    self.descWriteln('Traceback:')
    self.descWriteln('_%s_' % self.servletPathname())
    excInfo= self._exc
    out = apply(traceback.format_exception, excInfo)
    (filename, function)= (None, None)
    for line in out:
      if string.find(line, 'File ') != -1:
        i1= line.find('"')
        if i1 > 0:
          i2= line.find('"', i1+1)
          if i2 > 0:
            filename= line[i1+1:i2]
            funcsep= ' in '
            i3= line.find(funcsep, i2 + 1)
            if i3 > 0:
              i4= line.find('\n', i3 + 1)
              function= line[i3 + len(funcsep):i4]
      for l in line.strip().split('\n'):
        self.descWriteln(l)
    if len(out) > 1 and filename is not None and function is not None:
      finalline= out[-1].strip()
      sys.stdout.flush()
      filename= os.path.splitext(os.path.basename(filename))[0]
      if filename.startswith('_'):
        fnparts= filename.split('_')
        filename= '%s.%s' % (fnparts[-2], fnparts[-1])
      self.reporttitle= "%-70.70s" % \
        ("incident in %s.%s: %s" % (filename, function, finalline))

