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


import GaleDB, Gale, UserPrefs, string, time, re, MySQLdb, YGaleClient
import sys, YDB, SiteHTML, urllib, datetime
from InstallSettings import settings

from AuthYammerPage import AuthYammerPage

# if there is a gap of this much time between two puffs in the log
# table, a "tear" is inserted to make a visual mark between
# conversations
TEAR_PERIOD= datetime.timedelta(seconds=3600)

class GaleClientYammerPage(AuthYammerPage):



  def awake(self, trans):
    if hasattr(trans, '_session'):
      AuthYammerPage.awake(self, trans)
      if hasattr(self, 'u'):
        AuthYammerPage.awake(self, trans)
        (self.message, self.error)= ('', None)
        self.logRows= self.u.getPrefLimit('logpager.puffcount', 1, 50)
        if self._request.hasValue('subs'):
          self.subs= self._request.value('subs')
          self.setSessField('subs', self.urlEncode(self.subs))
        else:
          self.subs= self.getSessField('subs')
          if not self.subs:
            self.subs= self.u['subs.quick'].split(':')[0]
          else:
            self.subs= self.urlDecode(self.subs)
        self.subs= self.subs.split()
        if self._request.hasField('index'):
          self.index= int(self._request.field('index'))
        else:
          self.index= 0
        if self._request.hasValue('stage'):
          self.stage= int(self._request.value('stage'))
        else:
          self.stage= 10


  def getPuffs(self):
    possubs= [s for s in self.subs if not s.startswith('-')]
    negsubs= [s[1:] for s in self.subs if s.startswith('-')]
    kc= self.getKillClauses() + [['loc', s] for s in negsubs]
    return GaleDB.fetchPuffs(possubs, self.getGaleId(),
                                 self.index, self.logRows, kc)

  def writeFullLogTable(self):
    barposition= self.u['resub.bar']
    self.u['last.activity']= int(time.time())
    barindex= 1
    if barposition == 'both' or barposition == 'top':
      self.writeln(self.calcPrevnext(barindex))
      barindex= barindex + 1
    self.writeLogTable()
    if barposition == 'both' or barposition == 'bottom':
      self.writeln(self.calcPrevnext(barindex))
      barindex= barindex + 1

  def writeLogTable(self):
    res= self._response
    try:
      puffbatch= self.getPuffs()
      res.write('<table class="puffview" id="logtable">')
      rcg= SiteHTML.rowClassGenerator()
      for i in range(len(puffbatch)):
        if i > 0:
          date1= puffbatch[i-1]['ssdate']
          date2= puffbatch[i]['ssdate']
          if date1 is not None and date2 is not None:
            if (date1 - date2) >= TEAR_PERIOD:
              res.write('<tr><td colspan="2"><hr></td></tr>\n')
        self.puffcallback(puffbatch[i], rcg)
      res.write('</table>')
    except MySQLdb.OperationalError, sqlcode:
      res.write("""
        <div><strong>SQL error #%d while fetching puffs for display:
        %s</strong></div>
        """ % sqlcode.args)

  def displayPrivateCheckForm(self):
    res= self._response
    lastPrivateConfirm= self.u['last.private.time']
    if not lastPrivateConfirm or lastPrivateConfirm == '':
      self.debugMessage("no last.private.time for user %s; u=%s" %
          (self.peekUsername(), self.u))
      lastPrivateConfirm= 0
      lastPrivateDisplay= ''
    else:
      lastPrivateConfirm= int(lastPrivateConfirm)
      lastPrivateConfirm= time.strftime('%Y-%m-%d %H:%M:%S',
          time.localtime(lastPrivateConfirm))
      lastPrivateDisplay= 'since ' + lastPrivateConfirm[0:-3]
    query= ("SELECT COUNT(*) FROM puffs_t p, " + \
            "tos_t t WHERE " + \
            "(t.cat = '%s' OR t.cat LIKE '%s') " + \
            "AND p.puffid=t.puffid AND " + \
            "p.ssdate > '%s'") % (self.getGaleId(),
            self.getGaleIdPat(), lastPrivateConfirm)
    curs= YDB.getCursor()
    (countl,)= YDB.executeQuery(curs, query, {})
    YDB.close(curs)
    count= countl[0]
    s= ''
    pronoun= 'it'
    if count > 1:
      s= 's'
      pronoun= 'them'
    if count > 0:
      url= self.getStrippedUri()
      res.write("""
        <p>
          <img align="middle" alt="new messages" src="/images/newmsg.png">
          <span class="error">%s new private message%s %s
            &nbsp; &nbsp;</span>
          <a href="%s?subs=&_action_=confirm+private"><img
            align="middle" alt="view now" src="/images/go.png"></a><a
            href="%s?subs=&_action_=confirm+private">View
            %s now</a>
            &nbsp;&nbsp;
          <a href="%s?_action_=confirm+private"><img
            align="middle" alt="already seen" src="/images/check.png"></a><a
            href="%s?_action_=confirm+private">I've seen
            %s</a>
            &nbsp;&nbsp;
        </p>
        """ % (count, s, lastPrivateDisplay, url, url, pronoun, url,
          url, pronoun))

  def modifyKeywords(self, cats, kwds):
    for kwdtostrip in ['q', 'url', 'fwd', 'fixed']:
      [kwds.remove(x) for x in kwds if x == kwdtostrip or
                                       x.startswith(kwdtostrip+'.')]
    if (self.index > 0):
      kwds.append('catchup')
    return string.join(cats + ['/'+x for x in kwds])

  def hasKeyword(self, kwd, kwds):
    return len([k for k in kwds if k == kwd or k.startswith(kwd +
      '.')]) > 0

  def puffcallback(self, puff, rcg, style=''):
    # pull handy stuff into variables
    sender= puff['from']
    to_locs= map(self.htmlEncode, puff['locations'])
    signature= puff['sender']
    keywords= map(self.htmlEncode, puff['keywords'])
    if keywords is None:
      keywords= []
    date= puff['date']
    if date is None:
      date= time.strftime('[%Y-%m-%d %H:%M:%S]',
                          time.localtime(time.time()))
    else:
      date= date.strftime('%Y-%m-%d %H:%M:%S')
    text= puff['body']
    if not text:
      text= '' 
    text= string.replace(self.htmlEncode(text), '\n', '<br>')
    text= re.sub('(http(s?)://[^][{} <>()]*)([]}),.]?(<| |$))',
      r'<a target="_blank" href="\1">\1</a>\3', text)
    quotelevels= 0
    newtext= []
    if self.hasKeyword('q', keywords) or \
        self.hasKeyword('fwd', keywords):
      quotelevels += 1
      newtext.append('<blockquote>')
    for i, line in enumerate(text.split('<br>')):
      if quotelevels > 0 and line.startswith('==='):
        newtext.append('</blockquote>')
        quotelevels -= 1
        line= line.lstrip('=')
        if len(line) > 0:
          newtext += [line, '<br>']
      else:
        newtext += [line, '<br>']
    newtext += ['</blockquote>'] * quotelevels
    text= ''.join(newtext)
    prestyle= ''
    if len([k for k in keywords if k == 'fixed' or
        k.startswith('fixed.')]) > 0:
      prestyle= 'style="font-family: monospace; white-space: pre;"'
    tos= string.join(to_locs + ['/'+x for x in keywords])
    tosresp= self.modifyKeywords(to_locs, keywords)
    keything= ''
    style= rcg.next() + style
    if puff['encrypted'] == 1:
      style= style + " private"
      whocan= 'Only ' + string.join(to_locs, ' and ') + \
        ' can see this message'
      keything= ('<img class="encrypted" src="/images/key.png" ' + \
        'alt="%s" ' + \
        'title="%s">') % (whocan, whocan)
    self._response.write("""
      <tr class="%s" id="puffid-%d">
      """ % (style, puff['puffid']))
    self._response.write(self.extraPuffColumn(puff))
    self._response.write(self.thumbCell(signature))
    self._response.write("""
        <td class="puff">
          <div class="header">
            <div class="location">
              To: %s
            </div>
            <div class="fromTime">
                From: %s
                &nbsp;&nbsp;%s
            </div>
          </div>
          <div class="body" %s>%s%s</div>
        </td>
      </tr>
      """ % (self.emitLoc(tos, tosresp), \
        self.emitUser(signature, sender), date, prestyle, keything, text))

  def extraPuffColumn(self, puff):
    return ''

  def thumbCell(self, signature):
    thumbnailscale= None
    if self.peekUsername() is not None and self.__dict__.has_key('u'):
      s= self.u['thumbnail.shrink']
      if s == 'half-size':
        thumbnailscale= 40
      elif s == 'none':
        return ''
    else:
      thumbnailscale= 40
    thumbpage= settings['thumbnailServerURL'] + '?' + \
      urllib.urlencode({'id': signature, 'ret': 'mugs'})
    args= {'id': signature, 'nopiggy': '0'}
    if thumbnailscale is not None:
      args['height']= str(thumbnailscale)
    thumbimg= self.hostRoot() + 'WK/Yammer/ThumbProxy?' + \
      urllib.urlencode(args)
    return """
        <td align="center" valign="top" class="thumb">
          <a target="_blank"
            href="%(thumbpage)s">
          <img alt="thumbnail for %(signature)s"
            src="%(thumbimg)s"></a>
        </td>
      """ % locals()


  def calcPrevnext(self, i):
    result= ""
    jsubs= string.join(self.subs)
    uri= self.getStrippedUri()
    result= result + """
      <td>
        <a href="%s?subs=%s&index=%s">&lt;&lt; older messages</a>
      </td>
        """ % (uri, jsubs, self.index + self.logRows)
    if self.index > 0:
      i= self.index - self.logRows
      if i < 0:
        i= 0
      result= result + """
      <td>
        <a href="%s?subs=%s&index=%s">newer messages &gt;&gt;</a>
      </td>
        """ % (uri, jsubs, i)
    result= """ 
            %s<td> 
            <form name="resubform%s" action="%s" method="post">
              <input type="hidden" name="index" value="0">
              <input type="hidden" name="stage" value="10">

              <input type="submit"
                value="resubscribe to:"
                >&nbsp;<input type="text" size="40"
            """ % (result, i, uri)
    if len(jsubs) > 0:
      result= result + """value="%s" """ % jsubs
    (defsel, privsel)= ('', '')
    defaultSubs= self.u['subs.quick'].split(':')[0]
    if jsubs == string.join(string.split(defaultSubs)):
      defsel= "selected"
    elif jsubs == '':
      privsel= "selected"
    result= result + """name="subs">
        <script type="text/javascript">
          document.writeln('<select name="subdropdown"');
          document.writeln('onchange="blitSub(document.resubform%s.subdropdown.value);resub();">');
          document.writeln('<option>(quick subscription list)</option>');
          document.writeln('<option value="" %s>private messages only</option>');
          document.writeln('<optgroup label="custom subscriptions">');
          """ % (i, privsel)
    for sub in self.u['subs.quick'].split(':'):
      sub= string.strip(sub)
      selected= ''
      if sub == jsubs:
        selected= 'selected'
      result= result + '''
      document.writeln('<option value="%s" %s>%s</option>')''' % \
        (sub, selected, sub)
    result= result + """
      document.writeln('</optgroup></select>')
      </script>
      </form>
      </td>"""
    if self.peekUsername() is not None:
      u= self.getUserPrefs()
      ar= self.getStrippedUri() + '?_action_='
      kf= self.hostRoot() + 'gale/killfile/?subs=%s' % jsubs
      if len(u['killfile.contents'].strip()) == 0:
        result += """ 
          <td>
          <span class="fromTime">No killfile set.</span>
          <a target="_top" href="%(kf)s">[create]</a>
          </td>
          """ % locals()
      elif u['killfile.on'] == 'yes':
        result += """ 
          <td>
          <span class="fromTime">Killfile on.</span>
          <a target="_top" href="%(kf)s">[edit]</a>
          <a href="%(ar)skf+off">[turn off]</a>
          </td>
          """ % locals()
      elif u['killfile.on'] == 'no':
        result += """ 
          <td>
          <span class="fromTime">Killfile off.</span>
          <a target="_top" href="%(kf)s">[edit]</a>
          <a href="%(ar)skf+on">[turn on]</a>
          </td>
          """ % locals()

    return '<table border="0"><tr>%s</tr></table>\n' % result



  def emitUser(self, signature, sender):
    s= ""
    if signature == "*unsigned*" or signature == "*unverified*":
      s= "<i>%s</i>" % signature
    else:
      sys.stdout.flush()
      (uls, ule)= self.userLink(signature)
      s= uls + self.renderGaleid(signature) + ule
    if sender is not None:
      s= s + " (" + sender + ")"
    return s
  
  def userLink(self, signature):
    return '<a href="javascript:blitSender(\'' + signature + '\')">', '</a>'


  def emitLoc(self, tos, tosresp):
    return """<a href="javascript:blitLocation('%s')">%s</a>""" % \
      (tosresp, tos)


  def renderGaleid(self, id):
    sigbits= string.split(id, '@', 1)
    if len(sigbits) > 1:
      return "<b>%s</b>@%s" % (sigbits[0], sigbits[1])
    else:
      return "<b>%s</b>" % (sigbits[0])


  def getKillClauses(self):
    if self.u['killfile.on'] == 'yes':
      return [e.split('=') for e in
        self.u['killfile.contents'].split(';')]
    else:
      return []

  def writePostForm(self):
    res= self._response
    req= self._request

    if hasattr(self, 'error') and self.error is not None:
      res.write("""
        <span class="error">
          Unable to send message.<br>
          <a target="_blank" href="/guest/#validlocations">%s</a>
        </span>
        <hr>""" % (self.error))
    message= self.message
    defaultLocation= settings['defaultPostLocation']
    if req.hasValue('locations'):
      defaultLocation= req.value('locations').decode('utf-8')
    sg= self.u['send.geometry'].lower().split('x')
    sendRows, sendCols= 5, 80
    if len(sg) == 1:
      sendRows= int(sg[0])
    elif len(sg) == 2:
      sendCols, sendRows= map(int, sg)
      if sendCols < 1: sendCols= 1
      if sendCols > 1000: sendCols= 1000
    else:
      self.debugMessage('send.geometry pref invalid for ' + \
        self.getUsername() + ': "' + self.u['send.geometry'] + \
        '"')
    if sendRows < 1: sendRows= 1
    if sendRows > 50: sendRows= 50
    selfUrl= self.getStrippedUri()
    #res.write(self.entitize("""
    a= """
      <form name="postform" method="post" action="%(selfUrl)s">
        <table class="puffsend" border="0" cellpadding="0" cellspacing="0">

          <tr>
            <td align="right" valign="top">
              <b>post to&nbsp;</b>
            </td>

            <td>
              <input size="40" type="text"
                value="%(defaultLocation)s"
                id="locations"
                name="locations">
            </td>
            <td>&nbsp;</td>
          </tr>

          <tr>
            <td align="right" valign="top">
              <b>message&nbsp;</b>
            </td>

            <td colspan="2">
              <textarea name="message"
                id="message"
                rows="%(sendRows)s"
                cols="%(sendCols)s"
                wrap="soft">%(message)s</textarea>


              <input name="post" type="submit" value="post">

              <input type="hidden" name="_action_" value="post message">
            </td>
          </tr>
        </table>
      </form>""" % locals()
    a= self.entitize(a)
    res.write(a)



  def actions(self):
    return AuthYammerPage.actions(self) + \
      ['post message', 'confirm private', 'kf on', 'kf off']

  def actionKfOn(self, trans):
    if self.peekUsername() is not None:
      self.u['killfile.on']= 'yes'
    self.writeHTML()

  def actionKfOff(self, trans):
    if self.peekUsername() is not None:
      self.u['killfile.on']= 'no'
    self.writeHTML()

  def actionPostMessage(self, trans):
    import traceback
    req= trans.request()
    locations= self.formDecode(req.field('locations'))
    message= self.formDecode(req.field('message'))
    private= self.getGaleId()
    try:
      gc= YGaleClient.YGaleClient()
      Gale.filetraces('before gsend %s, %s', private, locations)
      gc.gsend(private, locations.split(), message)
      Gale.filetraces('after gsend %s, %s', private, locations)
      #gc.gsend(private, locations.encode('utf-8').split(), message)
      self.message= ''
    except Gale.PyGaleErr, x:
      traceback.print_tb(sys.exc_info()[2])
      self.error= x
      self.message= message
    except ValueError, x:
      traceback.print_tb(sys.exc_info()[2])
      self.error= x
      self.message= message
    self.writeHTML()

  def actionConfirmPrivate(self, trans):
    self.u['last.private.time']= int(time.time())
    self.writeHTML()

