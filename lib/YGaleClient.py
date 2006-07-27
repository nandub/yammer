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


import Gale, KeyStore
from pygale.pygale import *
from InstallSettings import settings
import UserPrefs, YammerUtils
from pygale import gale_pack
from pygale import pygale

class YGaleClient(GaleClient):
  def __init__(self, hostname=None, retry=1):
    GaleClient.__init__(self, hostname, retry)

  def next_puffs2(self):
    puffs = []
    self.set_puff_callback(lambda p, puffs=puffs: puffs.append(p))
    self._engine.process()
    return puffs

  def supplementCategory(self):
    domains= settings['galeDomains'].split()
    cats= ['@%s/user/' % domain for domain in domains]
    return cats


  def gsend(self, signer, to, message, RETURN_RECEIPT=0):
    to_locs= [x for x in to if x[0] != '/']
    to_kwds= [x for x in to if x[0] == '/']
    if len(to_locs) == 0:
      return
    to_locs= map(pygale.expand_aliases, to_locs)
    ret= lookup_all_locations(to_locs)
    (send_locs, bad_locs, encr_recps)= ([], [], [])
    for (loc, recps) in ret:
      if recps is None:
        bad_locs.append(loc)
      else:
        send_locs.append(loc)
        for r in recps:
          if isinstance(r, str):
            encr_recps.append(r)
          else:
            encr_recps.append(r.name())
    if bad_locs:
      raise ValueError, 'Unable to resolve location: ' \
          + string.join(bad_locs) + '.'
    if '' in encr_recps:
      # no point encrypting if we're also sending plaintext
      encr_recps= []
    else:
      if not signer in encr_recps:
        encr_recps.append(signer)
        to_locs.append(signer)
    puff= Puff()
    puff.set_loc(string.join(to_locs))
    u= UserPrefs.getInstance(signer)
    sender= u['gale.sender']
    if sender == '':
      sender= KeyStore.getFullname(signer)
    puff.set_text('message/sender', sender)
    puff.set_time('id/time', int(time.time()))
    puff.set_text('id/class', '%s/%s' % (settings['product'],
                                         YammerUtils.getVersionString()))
    puff.set_text('id/instance', getinstance())
    if RETURN_RECEIPT:
      puff.set_text('question.receipt', signer)
    for kwd in to_kwds:
      puff.set_text('message.keyword', kwd[1:])
    if len(message) > 0 and not message.endswith('\n'):
      message += '\n'
    puff.set_text('message/body', message)
    ret= puff.sign_message(signer)
    if ret is not None:
      # danger
      puff= ret
    if encr_recps:
      ret= puff.encrypt_message(encr_recps)
      if ret is not None:
        # danger
        puff= ret
    self.connect()
    self.transmit_puff(puff)
    self.disconnect()

  # messagecallback(message)
  # puffcallback(puff)
  def gsub(self, signer, subs, messagecallback, puffcallback):
    host= self.connect()
    if host is None:
      raise EOFError, 'Unable to connect to a gale server.'
    messagecallback('Connected to gale server %s.' % host)
    sender= getFullname(signer)
    notify_in('in.present', self, fullname=sender)
    notify_in('out.disconnected', self, fullname=sender)
    if signer not in subs:
      subs.append(signer)
    bad, good= self.sub_to(subs)
    if bad:
      for b in bad:
        messagecallback('Unable to find location %s.' % b)
    if not good:
      raise EOFError, 'No valid locations to subscribe to.'
    else:
      for g in good:
        messagecallback('Subscribed to %s.' % g)
    keepitup= 1
    while keepitup:
      puffs= self.next_puffs2()
      for puff in puffs:
        keepitup= puffcallback(puff)
        if not keepitup: break


