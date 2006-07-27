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


from YammerPage import YammerPage

import os.path, glob

class StaticYammerPage(YammerPage):
  def staticContent(self):
    req= self._request
    reqUri= req._environ['REQUEST_URI']
    path= os.path.dirname(req._environ['DOCUMENT_ROOT'] + reqUri)
    if req.hasField('txt'):
      txt= req.field('txt')
      txtf= open(path + '/' + txt)
      self.writeln('<pre>')
      while 1:
        line= txtf.readline()
        if not line:
          break
        self.write(self.htmlEncode(line))
      self.writeln('</pre>')
    else:
      txts= glob.glob(path + "/*.txt")
      if len(txts) > 0:
        self.writeln('<ul>')
        for txt in txts:
          txt= os.path.basename(txt)
          self.writeln('<li>')
          self.writeln('<a href=%s?txt=%s>%s</a>' %
                       (reqUri, self.urlEncode(txt), txt))
          self.writeln('</li>')
        self.writeln('</ul>')
      else:
        self.writeln('<b>no text files</b>')
