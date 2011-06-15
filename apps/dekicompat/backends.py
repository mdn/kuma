from urllib2 import build_opener, HTTPError
from xml.dom import minidom

from django.conf import settings
from django.contrib.auth.models import User

import commonware

from devmo.models import UserProfile

log = commonware.log.getLogger('mdn.dekicompat')

class DekiUserBackend(object):
    """
    This backend is to be used in conjunction with the 
    ``DekiUserMiddleware`` to authenticate via Dekiwiki.

    Tips for faking out Django/Dekiwiki https://intranet.mozilla.org/Webdev:MDN:DjangoAuth    
    """
    profile_url = "%s/@api/deki/users/current" % settings.DEKIWIKI_ENDPOINT
    profile_by_id_url = "%s/@api/deki/users/%s" % ( settings.DEKIWIKI_ENDPOINT, '%s' )

    def authenticate(self, authtoken):
        """
        We delegate to dekiwiki via an authtoken.
        """
        user = None
        opener = build_opener()
        auth_cookie = 'authtoken="%s"' % authtoken
        opener.addheaders = [('Cookie', auth_cookie),]
        resp = opener.open(DekiUserBackend.profile_url)
        deki_user = DekiUser.parse_user_info(resp.read())
        if deki_user:
            log.info("MONITOR Dekiwiki Auth Success")
            return self.get_or_create_user(deki_user)
        else:
            log.info("MONITOR Dekiwiki Failed")
            return None

    def get_deki_user(self, deki_user_id):
        """Fetch details for a given Dekiwiki profile by user ID"""
        opener = build_opener()
        resp = opener.open(DekiUserBackend.profile_by_id_url % deki_user_id)
        return DekiUser.parse_user_info(resp.read())

    def get_user(self, user_id):
        """Get a user for a given ID, used by auth for session-cached login"""
        try:
            user = User.objects.get(pk=user_id)
            profile = UserProfile.objects.get(user=user)
            user.deki_user = self.get_deki_user(profile.deki_user_id)
            return user
        except User.DoesNotExist:
            return None
        except HTTPError:
            return None

    def get_or_create_user(self, deki_user):
        """
        Grab the User via their UserProfile and deki_user_id. 
        If non exists, create both.

        NOTE: Changes to this method may require changes to
              parse_user_info
        """
        try:
            profile = UserProfile.objects.get(deki_user_id=deki_user.id)
            user = profile.user
            log.info("MONITOR Dekiwiki Profile Loaded")
            log.debug("User account already exists %d", user.id)
        except UserProfile.DoesNotExist:
            log.debug("First time seeing deki user id#%d username=%s, creating account locally", deki_user.id, deki_user.username)
            user, created = User.objects.get_or_create(username=deki_user.username)

            user.username = deki_user.username
            # HACK: Deki has fullname Django has First and last...
            # WACK: but our Dekiwiki instace doesn't let the user edit this data
            user.first_name = deki_user.fullname
            user.last_name = ''
            user.set_unusable_password()
            user.save()
            profile = UserProfile(deki_user_id = deki_user.id, user=user)
            profile.save()
            log.info("MONITOR Dekiwiki Profile Saved")
            log.debug("Saved profile %s", str(profile))
        user.deki_user = deki_user

        # Items we don't store in our DB (API read keeps it fresh)
        user.is_superuser = deki_user.is_superuser
        user.is_staff = deki_user.is_staff
        user.is_active = deki_user.is_active
        return user

class DekiUser(object):
    """
    Simple data type for deki user info
    """
    def __init__(self, id, username, fullname, email, gravatar, profile_url=None):
        self.id = id
        self.username = username
        self.fullname = fullname
        self.email    = email
        self.gravatar = gravatar
        self.profile_url  = profile_url
        self.is_active    = False
        self.is_staff     = False
        self.is_superuser = False

    @staticmethod
    def parse_user_info(xmlstring):
        """
        Parses XML and creates a DekiUser instance.
        If the user is Anonymous returns None.
        if the user is logged in, returns the DekiUser
        instace.

        NOTE: Updating this method may require changes to
              get_or_create_user

        TODO: Flesh out with more properties as needed.
        In the future we can support is_active, groups, etc.

        Example output form Deki:
<user id="115908">
    <nick>Anonymous</nick>
    <username>Anonymous</username>
    <fullname/>
    <email/>
    <hash.email>d41d8cd98f00b204e9800998ecf8427e</hash.email>
    <uri.gravatar>http://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e.png</uri.gravatar>
    <date.created>2005-03-15T23:42:24Z</date.created>
    <status>active</status>
    <date.lastlogin>2010-12-05T21:27:31Z</date.lastlogin>
    <language/>
    <timezone/>
    <service.authentication href="http://dekiwiki/@api/deki/site/services/1" id="1"/>
    <permissions.user><operations mask="15">LOGIN,BROWSE,READ,SUBSCRIBE</operations><role href="http://dekiwiki/@api/deki/site/roles/3" id="3">Viewer</role></permissions.user>
    <permissions.effective><operations mask="15">LOGIN,BROWSE,READ,SUBSCRIBE</operations></permissions.effective>
    <groups/>
    <properties count="0" href="http://dekiwiki/@api/deki/users/115908/properties"/>
</user>
        """
        xmldoc = minidom.parseString(xmlstring)
        deki_user = DekiUser(-1, 'Anonymous', '', '', 'http://www.gravatar.com/avatar/d41d8cd98f00b204e9800998ecf8427e.png')        

        userEl = None

        for c in xmldoc.childNodes:
            if c.nodeName == 'user':
                userEl = c
                break
        if not userEl:
            return None
        deki_user.id = int(userEl.getAttribute('id'))
        log.debug("Seeing user id %d", deki_user.id)

        deki_user.xml = xmlstring

        for c in userEl.childNodes:
            if 'username' == c.nodeName and c.firstChild:
                deki_user.username = c.firstChild.nodeValue
            elif 'fullname' == c.nodeName and c.firstChild:
                deki_user.fullname = c.firstChild.nodeValue
            elif 'email' == c.nodeName and c.firstChild:
                deki_user.email = c.firstChild.nodeValue
            elif 'uri.gravatar' == c.nodeName and c.firstChild:
                deki_user.gravatar = c.firstChild.nodeValue
            elif 'page.home' == c.nodeName:
                for sc in c.childNodes:
                    if 'uri.ui' == sc.nodeName and sc.firstChild:
                        deki_user.profile_url = sc.firstChild.nodeValue
            elif 'status' == c.nodeName:
                if 'active' == c.firstChild.nodeValue:
                    deki_user.is_active = True
            elif 'permissions.user' == c.nodeName:
                for sc in c.childNodes:
                    if 'role' == sc.nodeName:
                        if 'Admin' == sc.firstChild.nodeValue:
                            deki_user.is_staff = True
                            deki_user.is_superuser = True

        if 'Anonymous' == deki_user.username:
            return None
        else:
            return deki_user
