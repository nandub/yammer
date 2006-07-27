from YammerPage import YammerPage
from InstallSettings import settings
import os, urllib, sys

class ThumbProxy(YammerPage):
  def writeHTML(self):
    req= self._request
    res= self._response
    thumburl= settings['thumbnailServerURL']
    thumburl += '?' + req.environ()['QUERY_STRING']
    t= urllib.urlopen(thumburl)
    content= t.read()
    contentType= t.info().gettype()
    t.close()
    res.setHeader('Content-Type', contentType)
    res.setHeader('Content-Length', str(len(content)))
    sys.stdout.flush()
    res.write(content)

