from datetime import datetime
from urllib import urlencode
from urllib2 import HTTPError
import urlparse
import requests
from xml.dom import minidom
from xml.sax.saxutils import escape as xml_escape

from django.conf import settings
from django.contrib.auth.models import User

from pyquery import PyQuery as pq

import commonware

from devmo.models import UserProfile

# HACK: Using thread local to retain the authtoken used for Deki API requests
# on login
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local
_thread_locals = local()

log = commonware.log.getLogger('kuma.dekicompat')

MINDTOUCH_USER_XML = """<user><username>%(username)s</username><email>%(email)s</email><fullname>%(fullname)s</fullname><status>%(status)s</status><language>%(language)s</language><timezone>%(timezone)s</timezone><permissions.user><role>%(role)s</role></permissions.user></user>"""

class DekiUserBackend(object):
    """
    This backend authenticates via Dekiwiki. Should only activate
    if django login fails.
    """
    profile_url = "%s/@api/deki/users/current" % settings.DEKIWIKI_ENDPOINT
    profile_by_id_url = ("%s/@api/deki/users/%s" %
        (settings.DEKIWIKI_ENDPOINT, '%s'))
    users_by_email = ("%s/@api/deki/users?%s" %
        (settings.DEKIWIKI_ENDPOINT, '%s'))

    def authenticate(self, username=None, password=None):
        authtoken = DekiUserBackend.mindtouch_login(
            username=username,
            password=password)
        if authtoken:
            deki_user = DekiUserBackend.get_deki_user(url=DekiUserBackend.profile_url, 
                                                      authtoken=authtoken)
            if deki_user:
                # HACK: Retain authenticated authtoken for future Deki API
                # requests.
                _thread_locals.deki_api_authtoken = authtoken
                user = DekiUserBackend.get_or_create_user(deki_user)
                # Set django password equal to the password that authenticated
                # with MindTouch
                user.set_password(password)
                user.save()
                return user
            else:
                self.flush()
                return None
        else:
            return None

    def flush(self):
        """Flush any cached data"""
        _thread_locals.deki_api_authtoken = None

    @staticmethod
    def get_deki_user(deki_user_id=None, url=None, authtoken=None):
        """Fetch details for a given Dekiwiki profile by user ID"""
        if authtoken is None:
            authtoken = getattr(_thread_locals, 'deki_api_authtoken', None)
        cookies = {}
        if authtoken:
            # HACK: Use retained authenticated authtoken for future Deki API
            # requests. This gets us extra user details for the logged-in
            # user, such as email address.
            cookies = dict(authtoken=authtoken)
        if url is None:
            url = DekiUserBackend.profile_by_id_url % (str(deki_user_id) + 
                    '?apikey=' + settings.DEKIWIKI_APIKEY)
        resp = requests.get(url, cookies=cookies)
        if resp.status_code is 404:
            return None
        return DekiUser.parse_user_info(resp.read())

    @staticmethod
    def get_deki_user_id(resp):
        deki_user_id = None
        if resp.status_code is 200:
            doc = pq(resp.content)
            if len(doc('user')) > 1:
                most_recent_login = datetime(2000, 1, 1)
                deki_user_id = None
                for user in doc('user'):
                    last_login = datetime.strptime(user.find('date.lastlogin').text,
                                                   "%Y-%m-%dT%H:%M:%SZ")
                    if last_login > most_recent_login:
                        most_recent_login = last_login
                        deki_user_id = pq(user).attr('id')
            else:
                deki_user_id = doc('user').attr('id')
        return deki_user_id

    @staticmethod
    def get_deki_user_by_email(deki_user_email):
        """get_deki_user after an email query"""
        email_url = DekiUserBackend.users_by_email % urlencode(
            {'usernameemailfilter': deki_user_email,
            'apikey': settings.DEKIWIKI_APIKEY})
        resp = requests.get(email_url)
        deki_user_id = DekiUserBackend.get_deki_user_id(resp)
        if deki_user_id:
            return DekiUserBackend.get_deki_user(deki_user_id)
        else:
            return None

    def get_user(self, user_id):
        """Get a user for a given ID, used by auth for session-cached login"""
        try:
            user = User.objects.get(pk=user_id)
            profile = UserProfile.objects.get(user=user)
            user.deki_user = DekiUserBackend.get_deki_user(profile.deki_user_id)
            return user
        except User.DoesNotExist:
            return None
        except HTTPError:
            return None

    @staticmethod
    def get_or_create_user(deki_user):
        """
        Grab the User via their UserProfile and deki_user_id.
        If non exists, create both.

        NOTE: Changes to this method may require changes to
              parse_user_info
        """
        try:
            # Try fetching an existing profile mapped to deki user
            profile = UserProfile.objects.get(deki_user_id=deki_user.id)
            user = profile.user

        except UserProfile.DoesNotExist:
            # No existing profile, so try creating a new profile and user
            user, created = (User.objects
                             .get_or_create(username=deki_user.username))
            user.username = deki_user.username
            user.email = deki_user.email
            user.set_unusable_password()
            user.save()
            profile = UserProfile(deki_user_id=deki_user.id, user=user)
            profile.save()

        user.deki_user = deki_user

        # Sync these attributes from Deki -> Django (for now)
        sync_attrs = ('is_superuser', 'is_staff', 'is_active', 'email')
        needs_save = False
        for sa in sync_attrs:
            deki_val = getattr(deki_user, sa, None)
            if getattr(user, sa, None) != deki_val:
                setattr(user, sa, deki_val)
                needs_save = True

        if needs_save:
            user.save()

        return user

    @staticmethod
    def mindtouch_login(username, password, force=False):
        auth_url = "%s/@api/deki/users/authenticate" % (settings.DEKIWIKI_ENDPOINT)
        if force:
            auth_url = "%s/@api/deki/users/authenticate?apikey=%s" % (settings.DEKIWIKI_ENDPOINT, settings.DEKIWIKI_APIKEY)
            password = ''
        try:
            r = requests.post(auth_url, auth=(username.encode('utf-8'), password))
            if r.status_code == 200:
                authtoken = r.content
                return authtoken
            else:
                # TODO: decide WTF to do here
                return False
        except HTTPError:
            # TODO: decide WTF to do here
            return False

    @staticmethod
    def generate_mindtouch_user_xml(user):
        user_xml = MINDTOUCH_USER_XML % {'username': user.username,
                    'email': user.email,
                    'fullname': user.get_profile().fullname,
                    'status': 'active',
                    'language': user.get_profile().mindtouch_language,
                    'timezone': user.get_profile().mindtouch_timezone,
                    'role': 'Contributor'}
        return user_xml

    @staticmethod
    def post_mindtouch_user(user):
        # post a new mindtouch user
        user_url = '%s/@api/deki/users?apikey=%s' % (settings.DEKIWIKI_ENDPOINT,
                                                     settings.DEKIWIKI_APIKEY)
        user_xml = DekiUserBackend.generate_mindtouch_user_xml(user)
        headers = {'Content-Type': 'application/xml',}
        resp = requests.post(user_url, data=user_xml, headers=headers)
        if resp.status_code is not 200:
            # TODO: decide WTF to do here
            pass
        return DekiUser.parse_user_info(resp.content)

    @staticmethod
    def put_mindtouch_user(user):
        # update an existing mindtouch user
        deki_user_id = user.get_profile().deki_user_id or ''
        user_url = '%s/@api/deki/users/%s?apikey=%s' % (settings.DEKIWIKI_ENDPOINT,
                                                        deki_user_id,
                                                        settings.DEKIWIKI_APIKEY)
        user_xml = DekiUserBackend.generate_mindtouch_user_xml(user)
        headers = {'Content-Type': 'application/xml',}
        resp = requests.put(user_url, data=user_xml, headers=headers)
        if resp.status_code is not 200:
            # TODO: decide WTF to do here
            pass
        return DekiUser.parse_user_info(resp.content)


class DekiUser(object):
    """
    Simple data type for deki user info
    """
    def __init__(self, id, username, fullname, email, gravatar,
                 profile_url=None):
        self.id = id
        self.username = username
        self.fullname = fullname
        self.email = email
        self.gravatar = gravatar
        self.profile_url = profile_url
        self.is_active = False
        self.is_staff = False
        self.is_superuser = False

    def change_email(self, new_email, authtoken=None):
        """Given a new email address, attempt to change it for this user via
        the Deki API"""
        # No email change without authtoken
        authtoken = authtoken or getattr(_thread_locals,
                                         'deki_api_authtoken', None)
        if not authtoken:
            return

        import httplib
        try:
            auth_cookie = 'authtoken="%s"' % authtoken
            body = "<user><email>%s</email></user>" % (xml_escape(new_email))

            deki_tuple = urlparse.urlparse(settings.DEKIWIKI_ENDPOINT)
            if deki_tuple.scheme == 'https':
                conn = httplib.HTTPSConnection(deki_tuple.netloc)
            else:
                conn = httplib.HTTPConnection(deki_tuple.netloc)
            conn.request("PUT", '/@api/deki/users/%s' % self.id, body, {
                'Content-Type': 'text/xml',
                'Cookie': auth_cookie
            })
            resp = conn.getresponse()
            http_status_code = resp.status
            if http_status_code != 200:
                # TODO: decide WTF to do here
                # out = resp.read()
                pass
            conn.close()

        except httplib.HTTPException:
            return False

        return True

    @staticmethod
    def parse_user_info(xmlstring, authtoken=None):
        """
        Parses XML and creates a DekiUser instance.
        If the user is Anonymous returns None.
        if the user is logged in, returns the DekiUser
        instace.

        NOTE: Updating this method may require changes to
              get_or_create_user

        TODO: Flesh out with more properties as needed.
        In the future we can support is_active, groups, etc.
        """
        xmldoc = minidom.parseString(xmlstring)
        deki_user = DekiUser(-1, 'Anonymous', '', '',
                'http://www.gravatar.com/avatar/' +
                'd41d8cd98f00b204e9800998ecf8427e.png')

        userEl = None

        for c in xmldoc.childNodes:
            if c.nodeName == 'user':
                userEl = c
                break
        if not userEl:
            return None
        deki_user.id = int(userEl.getAttribute('id'))

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
            deki_user.authtoken = authtoken
            return deki_user
