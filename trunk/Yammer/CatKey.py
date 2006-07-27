from YammerPage import YammerPage
from InstallSettings import settings
import Gale, os


class CatKey(YammerPage):
  def writeHTML(self):
    req= self._request
    res= self._response
    if req.hasField('key'):
      which= req.field('key')
      username= self.getUsername()
      if username:
        user= self.getUsername()
        path= None
        if which == 'pri':
          path= Gale.privPath(user)
        elif which == 'pub':
          path= Gale.pubPath(user)
        if path:
          fp= open(path, 'r')
          content= fp.read()
          res.setHeader('Content-Type', 'application/octet-stream')
          res.setHeader('Content-Length', str(len(content)))
          res.setHeader('Content-Disposition', 'inline; ' + \
            'filename=' + os.path.basename(path))
          res.write(content)
        else:
          res.write("bad key header")
    else:
      res.write("meow meow")
