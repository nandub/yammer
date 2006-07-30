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


from WebKit.Page import Page
import MySQLdb, re, string, sys, YammerUtils
import YDB, os, UserPrefs, md5, time, smtplib, random
import LDAPUtilities
from InstallSettings import settings
from WebKit.Cookie import Cookie
from UserUtilities import *
from KeyStore import *
import threading

class YammerPage(Page):
  '''
  Superclass of all yammer.net servlets; intended to provide uniform
  look and feel.
  '''

  theFarPast= "Thu, 01 Dec 1994 16:00:00 GMT"
  segMethods= {'bannersidebar': 'bannersidebarSegment',
               'content': 'contentSegment'}

  def __init__(self):
    Page.__init__(self)
    self.loginError= None
    self.segURLs= {}
    self.mobilesettings= {'front.page': '/gale/logbased/consolidated.psp',
                          'resub.bar': 'bottom',
                          'do.autorefresh': 'no',
                          'compact.display': 'yes',
                          'thumbnail.shrink': 'none',
                          'show.menubar': 'no',
                          'mobile.mode': 'yes'}

  def awake(self, trans):
    Page.awake(self, trans)
    self.errorMessage= None
    self.noticeMessage= None
    self._transaction= trans
    self._request= trans.request()
    self._response= trans.response()
    u= self.getUserPrefs()
    self.internalUserStore= settings['userStore'] == 'internal'
    if u is not None:
      self.u= u

  def setMobileMode(self):
    u= self.getUserPrefs()
    for setting in self.mobilesettings.keys():
      value= self.mobilesettings[setting]
      if setting == 'thumbnail.shrink' and \
          u['thumbnail.shrink'] != 'none':
        value= 'half-size'
      u.setSessionPref(setting, value)

  def clearMobileMode(self):
    u= self.getUserPrefs()
    for setting in self.mobilesettings.keys():
      u.eraseSessionPref(setting)

  # subclasses may override
  def requiresAuth(self):
    return 0

  def customPageDraw(self):
    return 0

  def classTitle(self):
    return Page.title(self)

  def title(self):
    return settings['siteName']

  def actions(self):
    return ['log in', 'log out', 'mobile mode', 'clear mobile mode',
            'show menubar', 'hide menubar']

  def handleAction(self, action):
    if 0 and self.requiresAuth() and not self.getUsername():
      self.redirectToGuestRoot()
    else:
      methodName= self.methodNameForAction(action)
      apply(getattr(self, methodName), (self._transaction,))

  
  def methodNameForAction(self, name):
    methodName= 'action' 
    for word in string.split(name):
      methodName= methodName + string.capitalize(word)
    return methodName

  def getStylesheetPath(self):
    return settings['yammerRoot'] + '/Yammer/css/'

  def writeHeadParts(self):
    Page.writeHeadParts(self)
    self.writeFavico()


  def writeFavico(self):
    self.writeln('''
              <link rel="icon" type="image/png"
                href="/images/favicon.png">
                ''')

  def writeStyleSheet(self):
    u= self.getUserPrefs()
    base= '_compact'
    if u:
      stylesheet= u['stylesheet']
      base= '_base'
      if u.has_key('compact.display'):
        if u['compact.display'] == 'yes':
          base= '_compact'
    else:
      stylesheet= self.defaultStylesheet()
    if not os.path.exists(self.getStylesheetPath() + \
      stylesheet + '.css'):
        stylesheet= self.defaultStylesheet()
    self.writeln('''
              <link rel="stylesheet" type="text/css"
                href="/css/%s.css">
              <link rel="stylesheet" type="text/css"
                href="/css/%s.css">
                ''' % (base, stylesheet))

  def pspTitle(self):
    t= self.classTitle()
    if re.match("_.*psp", t):
      t= re.sub("_.*Yammer(.*?)(_psp|_index_psp)", r"\1", t)
      t= string.join(string.split(t, "_"))
    return t

  def bannerTitle(self):
    return settings['siteName']

  def cornerTitle(self):
    self.writeln('<img align="middle" src="/images/yammer-light.png" ' + \
           'alt="Yammer">')


  def writeNotices(self):
    wr= self.writeln
    if self.errorMessage is not None:
      wr('<div class="error">%s</div>' % self.errorMessage)
    if self.noticeMessage is not None:
      wr('<div class="notice">%s</div>' % self.noticeMessage)

  def writeBody(self):
      # begin
      wr = self.writeln
      wr('<body>')
      wr('<table border="0" cellpadding="5" cellspacing="5" width="100%">')

      # banner
      if not self.suppressMenu():
        self.writeSidebar()
      wr('<tr>')
      wr('<td valign=top width=90%>')
      self.writeNotices()
      self.writeContent()
      wr('</td>')
      wr('</tr>')
      if self.suppressMenu():
        self.writeSidebar()

      # end
      wr('</table>')
      wr('</body>')



  def suppressMenu(self):
    u= self.getUserPrefs()
    return u is not None and u['show.menubar'] == 'no'

  def writeSidebar(self):
    self.writeln('<tr>')
    if self.suppressMenu():
      self.writeln('<td valign="top" align="right">')
      self.preMenuSidebar()
      self.writeln('<a href="?_action_=show+menubar">')
      self.cornerTitle()
      self.writeln('</a>')
      self.writeln('<a href="?_action_=show+menubar">' + \
        'show menubar')
      self.writeln('</a>')
    else:
      self.writeln('<td valign="top">')
      self.preMenuSidebar()
      self.startMenu()
      self.sidebarMenu()
      self.endMenu()
      self.postMenuSidebar()
    self.writeln('</td></tr>')




  def preMenuSidebar(self):
    pass


  def postMenuSidebar(self):
    self.writeln('<hr>')

  def sidebarMenu(self):
    self.writeln('<table><tr><td>')
    self.writeln('<td valign="top">')
    self.loginDoings()
    self.writeln('</td>')
    self.yammerMenu(self.horzMenuItem, self.horzMenuHeading)
    self.writeln('</td></tr></table>')
    iu= self.peekUsername()
    self.writeln('<td valign="top" align="right">')
    if iu is not None:
      self.writeln('<a href="?_action_=hide+menubar">')
    self.cornerTitle()
    if iu is not None:
      self.writeln('</a>')
      self.writeln('<a href="?_action_=hide+menubar">')
      self.writeln('hide menubar')
      self.writeln('</a>')
    self.writeln('</td>')

  def horzMenuHeading(self, title):
    if self._wroteHeading:
      self.writeln('</span></td><td>&nbsp;</td>')
    self.writeln('<td><b>%s</b><br><span class="menubottom">' % title)
    self._wroteHeading= 1

  def horzMenuItem(self, title, url=None, extra=None):
    if extra:
      extra = extra + ' '
    else:
      extra = ''
      if url is not None:
        if url[0] == '/':
          target= "_top"
        else:
          target= "_blank"
        self.writeln('<a href="%s" target="%s">%s</a> %s' \
          % (url, target, title, extra))
      else:
        self.writeln('%s %s' % (title, extra))


  def startMenu(self):
      self.writeln('<table width="100%"><tr>')
      self._wroteHeading = 0

  def endMenu(self):
      self.writeln('</tr></table>')

  def loginDoings(self):
    username= self.getUsername()
    if username:
      self.logoutForm(username)
    else:
      self.loginForm()
    self.loginError= None

  def loginForm(self):
    if self.loginError:
      self.writeln('''
        <p align="center">
          <large>
            <span class="error">
              %s
            </span>
          </large>
        </p>
      ''' % (self.loginError))
    if self.internalUserStore:
      self.writeln('''
        <a href="/register/">Sign up</a> or log in
        here if you already have an account.''')
    else:
      self.writeln('''
        Log in with your user id and password from LDAP.''')
    self.writeln('''
      <p>
      <form name="login" method="post">
        <b>username:</b>
        <br>
        ''')
    self.writeUsernameInputs()
    self.writeln('''
        <br>
        <b>password:</b>
        <br>
        <input type="password" name="password" size="8">
        <br>
        <input type="checkbox" name="noautologin">
        This is a shared, public computer.
        <br>
        <input name="_action_" type="submit" value="log in">
      </form>
      <p>''')
    if self.internalUserStore:
      self.writeln('''
        <a href="/register/forgot.psp">Forgot your password?</a>
      ''')

  def writeUsernameInputs(self):
    self.writeln('''
        <input name="username" size="8"
          style="text-align:right">
          ''')
    domains= settings['galeDomains'].split()
    if len(domains) == 1:
      self.writeln('''
        <input type="hidden" name="domain" value="%s">
        <span>@%s</span>''' % (domains[0], domains[0]))
    else:
      self.writeln('''<select name="domain">''')
      for domain in domains:
        self.writeln('<option value="%s">@%s</option>' % (domain,domain))
      self.writeln('''</select>''')

  def logoutForm(self, username):
    pass

  def yammerMenu(self, mi, mh):
    username= self.getUsername()
    if username:
      mh(username)
      mi('home', '/')
      mi('preferences', '/preferences/')
      if self.internalUserStore:
        mi('password', '/preferences/password.psp')
      #mi('keypair', '/keys/')
      mi('log out', '/?_action_=log+out')
      u= self.getUserPrefs()
      if u['mobile.mode'] == 'yes':
        mi('mobile mode off', '/?_action_=clear+mobile+mode')
      else:
        mi('mobile mode', '/?_action_=mobile+mode')
    mh('Yammer')
    mi('help', '/guest/')
    mi('logs', '/logs/')
    mi('today', '/logs/?datestart=0:00&submit=skim')
    mi('known bugs', "http://code.google.com/p/yammer/issues/list")
    mi('file bug or suggest feature', self.getFileTicketUrl())
    mh('Gale')
    mi('gale.org', 'http://gale.org/')
    mi('faq', 'http://wiki.ofb.net/?GaleFaq')
    self.writeln('</span></td>')

  def getFileTicketUrl(self):
    comment= 'Reported in version %s' % YammerUtils.getVersionString()
    username= self.getUsername()
    if username is not None:
      comment += ' by %s' % self.getGaleId()
    comment += '\n\nProblem description:\n'
    return 'http://code.google.com/p/yammer/issues/entry?comment=%s' % (
        self.urlEncode(comment))

  def writeContent(self):
    self.writeln("yammer.net")

  def attemptLogin(self, username, password):
    userstuff= checkPassword(username, password)
    if userstuff:
      req= self._transaction.request()
      if not req.hasField('noautologin'):
        self.generateAutologinCookie(username)
      self.logUserIn(username, userstuff)
      return 1
    return 0

  def generateAutologinCookie(self, username):
    hash= md5.new(username + str(time.time())).hexdigest()
    self.setPermanentCookie('autologin', username + ' ' + hash)
    prefs= UserPrefs.getInstance(username)
    prefs['autologin.hash']= hash

  def revokeAutologinCookie(self, username):
    self.deletePermanentCookie('autologin')
    prefs= UserPrefs.getInstance(username)
    prefs['autologin.hash']= ''

  def ldapProvision(self, username, userstuff):
    if not KeyStore.havePrivateFor(username):
      email, fullname= LDAPUtilities.getEmailAndFullName(userstuff)
      error= gkgen(username, fullname)
      if error is None:
        u= UserPrefs.getInstance(username)
        u['email.address']= email
      else:
        self.errorMessage= error
        return 0
    return 1




  def logUserIn(self, username, userstuff= None):
    self.setSessField('username', username)
    ok= 1
    if settings['userStore'].startswith('ldap'):
      ok= self.ldapProvision(username, userstuff)
    if ok:
      self.redirectToAuthRoot()
    else:
      self.logOut()
      self.writeHTML()

  def setPermanentCookie(self, key, value):
    cookie = Cookie(key, value)
    t = time.gmtime(time.time())
    t = (t[0] + 10,) + t[1:]
    t = time.strftime("%a, %d-%b-%Y %H:%M:%S GMT", t)
    cookie.setExpires(t)
    cookie.setPath('/')
    self.response().addCookie(cookie)

  def deletePermanentCookie(self, key):
    cookie = Cookie(key, '')
    t = time.gmtime(time.time())
    t = (t[0] - 10,) + t[1:]
    t = time.strftime("%a, %d-%b-%Y %H:%M:%S GMT", t)
    cookie.setExpires(t)
    cookie.setPath('/')
    self.response().addCookie(cookie)

  def defaultStylesheet(self):
    return 'gray'

  # see if there is a username without doing autologin madness
  def peekUsername(self):
    trans= self._transaction
    if trans.hasSession():
      session= trans.session()
      if session.hasValue('username'):
        return session.value('username')
    return None

  # get username (after logging in automatically, if there is a
  # cookie)
  def getUsername(self):
    return self.getSessField('username')

  def isLoggedIn(self):
    return self.getUsername()

  def getGaleId(self):
    return self.getUsername()

  def getGaleIdPat(self):
    u,d= self.getUsername().split('@')
    return u + '.%%@' + d

  def setSessField(self, fieldname, fieldvalue):
    self._transaction.session().setValue(fieldname, fieldvalue)

  def getSessField(self, fieldname):
    trans= self._transaction
    sess= self.getSession()
    if sess is not None:
      if sess.hasValue(fieldname):
        return sess.value(fieldname)
    return None

  def getSession(self):
    trans= self._transaction
    req= trans.request()
    if not trans.hasSession() and req.hasCookie('autologin'):
      cook= req.cookie('autologin')
      if cook is not None:
        (user, hash)= cook.split()
        if hash is not None:
          prefs= UserPrefs.getInstance(user)
          correcthash= prefs['autologin.hash']
          if correcthash is not None and hash == correcthash:
            self.logUserIn(user)
    if trans.hasSession():
      return trans.session()
    return None





  # fetch current user's preferences from database
  def getUserPrefs(self):
    username= self.getUsername()
    if username:
      return UserPrefs.SessionUserPrefs(UserPrefs.getInstance(username),
          self._transaction)


  def hostRoot(self):
    req= self._request
    protocol= 'http://'
    if self.isSSLed():
      protocol= 'https://'
    return protocol + req._environ['HTTP_HOST'] + '/'

  # utility to automatically redirect the browser
  def redirect(self, target):
    res= self._response
    res.sendRedirect(target)
    self.debugMessage('redirect target=%s' % target)
    res.setStatus(302)

  def slowRedirect(self, message, target):
    self.writeln('''
      <html>
        <head>
          <meta http-equiv="refresh"
                            content="3; url=%(target)s">
          <title>%(message)s</title>
        </head>
        <body>
          <p>
            %(message)s
          </p>
          <p>
            <a href="%(target)s">
              Click here if you aren't redirected within 5 seconds.
            </a>
          </p>
        </body>
      </html>
      ''' % locals())
    

  def redirectToAuthRoot(self):
    #self.redirect(self.hostRoot())
    pass

  # when first bounced, go to /guest/
  def redirectToGuestRoot(self):
    self.forwardTo('/guest/')
    #self.redirect(self.hostRoot() + 'guest/')

  def forwardTo(self, uri):
    self.transaction().application().forward(self.transaction(),
      uri)

  def goodPassword(self, password):
    return len(password) > 4




    

  def actionMobileMode(self, trans):
    self.setMobileMode()
    self.writeHTML()

  def actionClearMobileMode(self, trans):
    self.clearMobileMode()
    self.writeHTML()

  def actionShowMenubar(self, trans):
    u= self.getUserPrefs()
    u.setSessionPref('show.menubar', 'yes')
    self.writeHTML()

  def actionHideMenubar(self, trans):
    u= self.getUserPrefs()
    u.setSessionPref('show.menubar', 'no')
    self.writeHTML()

  def actionLogIn(self, trans):
    self.debugMessage('attempting log in for user: ' +
        self._request.field('username'))
    sys.stdout.flush()
    self.loginError= None
    req= self._request
    self.loginError= 'helllooooo'
    if req.hasField('username') and req.hasField('domain') and \
        req.hasField('password'):
      username= req.field('username')
      domain= req.field('domain')
      password= req.field('password')
      if not self.attemptLogin(username + '@' + domain, password):
        self.loginError= 'authentication failed'
    else:
      self.loginError= 'arguments garbled'
    self.writeHTML()

  def logOut(self):
    username= self.peekUsername()
    self.session().invalidate()
    if username is not None:
      self.revokeAutologinCookie(username)

  def actionLogOut(self, trans):
    self.logOut()
    self.redirect(self.hostRoot())


    
  def writeHTML(self):
    if self.requiresAuth() and not self.getUsername():
      self.redirectToGuestRoot()
    else:
      if self.shouldUseFrames():
        self.doFrameCraziness()
      else:
        if not self.customPageDraw():
          self._response.setHeader("Expires", self.theFarPast)
          Page.writeHTML(self)

  # override this method if you want to use frames, or use them
  # conditionally
  def shouldUseFrames(self):
    return 0

  def debugMessage(self, message):
    YammerUtils.debugMessage(message)


  def doFrameCraziness(self):
    req= self._request
    if req.hasValue('segment'):
      segment= req.value('segment')
      assert self.segMethods.has_key(segment)
      apply(YammerPage.__dict__[self.segMethods[segment]], [self])
    else:
      self.framesetSegment()

  def framesetSegment(self):
    url= self._request._environ['REQUEST_URI']
    title= self.title()
    assert url != None and len(url) > 0
    urls= {}
    for u in self.segMethods.keys():
      if self.segURLs.has_key(u):
        urls[u]= self.segURLs[u]
      else:
        urls[u]= url + '?segment=' + u

    self.writeln("""
      <html>
        <head>
        """)
    self.writeHeadParts()
    self.writeln("""
        </head>
        <frameset cols="*">
          <frame src="%(content)s" scrolling="no"
            name="content">
          <noframes>
            Sorry, this document can only be viewed with a
            frames-capable browser.
            You can
            <a href="/gale/logbased/consolidated.psp">use 
            the frameless version</a>.  If you always want to use
            the frameless version, you can choose it in your user 
            preferences.
          </noframes>
        </frameset>
      </html>
    """ % urls)

  def bannersidebarSegment(self):
    wr= self.writeln
    wr('<html><head>')
    self.writeHeadParts()
    wr('</head><body>')
    wr("<table border=0 cellpadding=0 cellspacing=0 width=100%>")
    wr('<tr>')
    wr('<td width="200">')
    self.cornerTitle()
    wr('</td>')
    wr('</tr>')
    wr('<tr> <td width="200" valign=top>')
    self.writeSidebar()
    wr('</td></tr>')
    wr("</table>")
    wr('</body></html>')

  def contentSegment(self):
    self.writeln('<html><body bgcolor="white">')
    self.writeContent()
    self.writeln('</body></html>')

  def getStrippedUri(self):
    uri= self._request.environ()['SCRIPT_URI']
    #uri= 'http://%s%s' % (self._request.environ()['HTTP_HOST'],
      #self._request.environ()['SCRIPT_URL'])
    uriparts= uri.split('/')
    if uriparts[-1] == 'index' or uriparts[-1] == 'index.psp':
      uri= string.join(uriparts[0:-1], '/') + '/'
    return uri

  def writeExceptionReport(self, handler):
    handler.writeTitle(self.pspTitle())
    handler.writeln('object fields:')
    handler.writeDict(self.__dict__)
    u= self.getUserPrefs()
    if u:
      handler.writeln('user preferences:')
      # ... danger!
      handler.writeDict(u)

  def htmlEncode(self, s):
    s= Page.htmlEncode(self, s)
    return self.entitize(s)

  def entitize(self, s):
    s1= []
    for c in s:
      if ord(c) > 0x7f:
        c= '&#x%04x;' % ord(c)
      s1.append(c)
    return ''.join(s1)

  def formDecode(self, s):
    if isinstance(s, str):
      s= s.decode('utf8')
    return re.sub(r'&#(\d+);', lambda m: unichr(int(m.group(1))),
        unicode(s))


  def isSSLed(self):
    env= self.request().environ()
    return env is not None and env.has_key('HTTPS') and env['HTTPS'] == 'on'
