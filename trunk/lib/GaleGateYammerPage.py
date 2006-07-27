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


from AuthYammerPage import AuthYammerPage
from YammerPage import YammerPage
import Gale, sys, KeyStore
from InstallSettings import settings

class GaleGateYammerPage(AuthYammerPage):

  def __init__(self):
    AuthYammerPage.__init__(self)
    self.gkgenMessage= None

  def actions(self):
    return AuthYammerPage.actions(self) + ['generate']

  def actionGenerate(self, trans):
    req= self._request
    fullname= ''
    if req.hasField('fullname'):
      fullname= req.field('fullname')
    self.gkgenMessage= KeyStore.gkgen(self.getGaleId(), fullname)
    if self.gkgenMessage is not None:
      self.redirectToAuthRoot()
    else:
      self.writeHTML()

  def customPageDraw(self):
    if self.hasPrivateKey():
      self.redirect(self.getUserPrefs()['front.page'])
      return 1
    return 0


  def hasPrivateKey(self):
    privateKey= self.getUsername()
    return KeyStore.havePrivateFor(privateKey)

  def shouldUseFrames(self):
    if self.hasPrivateKey():
      prefs= self.getUserPrefs()
      frontPage= prefs['front.page']
      if frontPage.endswith('frameset.psp'):
        self.segURLs['content']= '/gale/logbased/frameset.psp'
        return 1
      else:
        return 0
    else:
      return 0
