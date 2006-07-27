from YammerPage import YammerPage
from InstallSettings import settings
import Gale, os

class MdkClientDownload(YammerPage):
  def writeHTML(self):
    req= self._request
    res= self._response
    mdkclient= settings['yammerRoot'] + '/bin/mdk'
    m= open(mdkclient, 'r')
    content= m.read()
    m.close()
    res.setHeader('Content-Type', 'application/octet-stream')
    res.setHeader('Content-Length', str(len(content)))
    res.setHeader('Content-Disposition', 'inline; ' + \
      'filename=' + os.path.basename(mdkclient))
    res.write(content)

