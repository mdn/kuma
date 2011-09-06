from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.translation import ugettext_lazy as _

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from PIL import Image
except ImportError:
    import Image

DEMOS_CACHE_NS_KEY = getattr(settings, 'DEMOS_CACHE_NS_KEY', 'demos_listing')

# HACK: For easier L10N, define tag descriptions in code instead of as a DB model
TAG_DESCRIPTIONS = dict( (x['tag_name'], x) for x in getattr(settings, 'TAG_DESCRIPTIONS', (

    {
        "tag_name": "challenge:2011:june", 
        "title": _("June 2011 Dev Derby Challenge - CSS3 Animations"), 
        "short_title": _("CSS3 Animations"),
        "dateline": _("June 2011"),
        "short_dateline": _("June"),
        "tagline": _("Style and experience"),
        "summary": _("CSS3 Animations let you change property values over time, to animate the appearance or position of elements, with no or minimal JavaScript, and with greater control than transitions."),
        "description": _("CSS3 Animations are a new feature of modern browsers like Firefox, which add even more flexibility and control to the style and experience of the Web. CSS3 Animations let you change property values over time with no or minimal JavaScript, and with greater control than CSS Transitions. Go beyond static properties to animate the appearance and positions of HTML elements. You can achieve these effects without Flash or Silverlight, to make creative dynamic interfaces and engaging animations with CSS3."),
        "learn_more": [],
    },
    {
        "tag_name": "challenge:2011:july", 
        "title": _("July 2011 Dev Derby Challenge - HTML5 <video>"), 
        "short_title": _("HTML5 <video>"),
        "dateline": _("July 2011"),
        "short_dateline": _("July"),
        "tagline": _("Lights, camera, action!"),
        "summary": _("The HTML5 <video> element lets you embed and control video media directly in web pages, without resorting to plug-ins."),
        "description": _("The HTML5 <video> element lets you embed and control video media directly in web pages, without resorting to plug-ins."),
        "learn_more": [],
    },
    {
        "tag_name": "challenge:2011:august", 
        "title": _("August 2011 Dev Derby Challenge - History API"), 
        "short_title": _("History API"),
        "dateline": _("August 2011"),
        "short_dateline": _("August"),
        "tagline": _("A browser never forgets"),
        "summary": _("The History API in modern browsers enables live changes to the document without breaking the back button and allows apps to be bookmarked."),
        "description": _("The History API in modern browsers enables live changes to the document without breaking the back button and allows apps to be bookmarked."),
        "learn_more": [],
    },
    {
        "tag_name": "challenge:2011:september", 
        "title": _("September 2011 Dev Derby Challenge - Geolocation"), 
        "short_title": _("Geolocation"),
        "dateline": _("September 2011"),
        "short_dateline": _("September"),
        "tagline": _("You are HERE"),
        "summary": _("With Geolocation, you can get the user's physical location (with permission) and use it to enhance the browsing experience or enable advanced location-aware features."),
        "description": _("With Geolocation, you can get the user's physical location (with permission) and use it to enhance the browsing experience or enable advanced location-aware features."),
        "learn_more": [],
        "tab_copy": _("""<p>Mobile device users are by now accustomed to "checking in" and getting directions using their devices. The Geolocation API enables web developers to offer features based on the user's location without having to call a native API, much less having to submit an app to a gatekeeper or require the user to install yet another native app.</p>
<p>With information bout the user's location and movement, you could provide a local guide (say, a muggle's guide to magical London), invent location-based games, or apply global datasets to any location (such as your local weather trends 50 years from now, based on climate change predications).</p>
<p>Note that the judges may not be able to fully test demos that are specific to remote locations, so a video of such demos is very helpful. Though if we were to get several submissions about Caribbean islands ...</p>"""),
    },
    {
        "tag_name": "challenge:2011:october", 
        "title": _("October 2011 Dev Derby Challenge - CSS Media Queries"), 
        "short_title": _("CSS Media Queries"),
        "dateline": _("October 2011"),
        "short_dateline": _("October"),
        "tagline": _("Size does matter"),
        "summary": _("CSS Media Queries allow Web developers to create responsive Web designs, tailoring the user experience for a range of screen sizes, including desktops, tablets, and mobiles."),
        "description": _("CSS Media Queries allow Web developers to create responsive Web designs, tailoring the user experience for a range of screen sizes, including desktops, tablets, and mobiles."),
        "learn_more": [],
        "tab_copy": _("""<p>The range of hardware that can display Web pages is increasing exponentially. Feature phones, smart phones, tablets, e-book readers, game consoles, video players, and high-res widescreen displays now co-exist with the basic laptop and desktop screens of just a few years ago. Older techniques for adapting to device size, such as relying on user agent strings, become impractical with this explosion of diversity. Fortunately, CSS3 media queries enable you to tailor your design based on the physical characteristics of the display device, which is the relevant factor anyway.</p>
<p>Not just layout, but typography, navigation, and hot spots can all adapt to provide an optimal Web experience for the device of the moment, as the same content shines everywhere.</p>"""),
    },
    {
        "tag_name": "challenge:2011:november", 
        "title": _("November 2011 Dev Derby Challenge - Canvas"), 
        "short_title": _("Canvas"),
        "dateline": _("November 2011"),
        "short_dateline": _("November"),
        "tagline": _("The joy of painting"),
        "summary": _("Canvas lets you to paint the Web using JavaScript to render 2D shapes, bitmapped images, and advanced graphical effects.  Each <canvas> element provides a graphics context with its own state and methods that make it easy to control and draw in."),
        "description": _("Canvas lets you to paint the Web using JavaScript to render 2D shapes, bitmapped images, and advanced graphical effects.  Each <canvas> element provides a graphics context with its own state and methods that make it easy to control and draw in."),
        "learn_more": [],
        "tab_copy": _("Canvas lets you to paint the Web using JavaScript to render 2D shapes, bitmapped images, and advanced graphical effects.  Each <canvas> element provides a graphics context with its own state and methods that make it easy to control and draw in."),
    },


    { 
        "tag_name": "tech:audio", 
        "title": _("Audio"), 
        "description": _("Mozilla's Audio Data API extends the current HTML5 API and allows web developers to read and write raw audio data."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/Introducing_the_Audio_API_Extension')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/HTML5_audio')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/html5/video.html#audio')),
        ),
    },
    { 
        "tag_name": "tech:canvas", 
        "title": _("Canvas"),
        "description": _("The HTML5 canvas element allows you to display scriptable renderings of 2D shapes and bitmap images."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/HTML/Canvas')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Canvas_element')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/html5/the-canvas-element.html')),
        ),
    },
    { 
        "tag_name": "tech:css3", 
        "title": _("CSS3"), 
        "description": _("Cascading Style Sheets level 3 (CSS3) provide serveral new features and properties to enhance the formatting and look of documents written in different kinds of markup languages like HTML or XML."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/CSS')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Cascading_Style_Sheets')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/css3-roadmap/')),
        ),
    },
    { 
        "tag_name": "tech:device", 
        "title": _("Device"), 
        "description": _("Media queries and orientation events let authors adjust their layout on hand-held devices such as mobile phones."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/Detecting_device_orientation')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/css3-mediaqueries/')),
        ),
    },
    { 
        "tag_name": "tech:files", 
        "title": _("Files"), 
        "description": _("The File API allows web developers to use file objects in web applications, as well as selecting and accessing their data."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/using_files_from_web_applications')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/FileAPI/')),
        ),
    },
    { 
        "tag_name": "tech:fonts", 
        "title": _("Fonts & Type"), 
        "description": _("The CSS3-Font specification contains enhanced features for fonts and typography like  embedding own fonts via @font-face or controlling OpenType font features directly via CSS."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/css/@font-face')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Web_typography')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/css3-fonts/')),
        ),
    },
    { 
        "tag_name": "tech:forms", 
        "title": _("Forms"), 
        "description": _("Form elements and attributes in HTML5 provide a greater degree of semantic mark-up than HTML4 and remove a great deal of the need for tedious scripting and styling that was required in HTML4."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/HTML/HTML5/Forms_in_HTML5')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/HTML_forms')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/html5/forms.html')),
        ),
    },
    { 
        "tag_name": "tech:geolocation", 
        "title": _("Geolocation"), 
        "description": _("The Geolocation API allows web applications to access the user's geographical location."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/En/Using_geolocation')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/W3C_Geolocation_API')),
            (_('W3C Spec'),          _('http://dev.w3.org/geo/api/spec-source.html')),
        ),
    },
    { 
        "tag_name": "tech:javascript",
        "title": _("JavaScript"), 
        "description": _("JavaScript is a lightweight, object-oriented programming language, commonly used for scripting interactive behavior on web pages and in web applications."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/javascript')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/JavaScript')),
            (_('ECMA Spec'),         _('http://www.ecma-international.org/publications/standards/Ecma-262.htm')),
        ),
    },
    { 
        "tag_name": "tech:html5",
        "title": _("HTML5"), 
        "description": _("HTML5 is the newest version of the HTML standard, currently under development."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/HTML/HTML5')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Html5')),
            (_('W3C Spec'),          _('http://dev.w3.org/html5/spec/Overview.html')),
        ),
    },
    { 
        "tag_name": "tech:indexeddb", 
        "title": _("IndexedDB"), 
        "description": _("IndexedDB is an API for client-side storage of significant amounts of structured data and for high performance searches on this data using indexes. "),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/IndexedDB')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/IndexedDB')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/IndexedDB/')),
        ),
    },
    { 
        "tag_name": "tech:dragndrop", 
        "title": _("Drag and Drop"), 
        "description": _("Drag and Drop features allow the user to move elements on the screen using the mouse pointer."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/DragDrop/Drag_and_Drop')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Drag-and-drop')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/html5/dnd.html')),
        ),
    },
    { 
        "tag_name": "tech:mobile",
        "title": _("Mobile"), 
        "description": _("Firefox Mobile brings the true Web experience to mobile phones and other non-PC devices."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/En/Mobile')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Mobile_web')),
            (_('W3C Spec'),          _('http://www.w3.org/Mobile/')),
        ),
    },
    { 
        "tag_name": "tech:offlinesupport", 
        "title": _("Offline Support"), 
        "description": _("Offline caching of web applications' resources using the application cache and local storage."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/dom/storage#localStorage')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Web_Storage')),
            (_('W3C Spec'),          _('http://dev.w3.org/html5/webstorage/')),
        ),
    },
    { 
        "tag_name": "tech:svg", 
        "title": _("SVG"), 
        "description": _("Scalable Vector Graphics (SVG) is an XML based language for describing two-dimensional vector graphics."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/SVG')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Scalable_Vector_Graphics')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/SVG11/')),
        ),
    },
    { 
        "tag_name": "tech:video", 
        "title": _("Video"), 
        "description": _("The HTML5 video element provides integrated support for playing video media without requiring plug-ins."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/En/Using_audio_and_video_in_Firefox')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/HTML5_video')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/html5/video.html')),
        ),
    },
    { 
        "tag_name": "tech:webgl", 
        "title": _("WebGL"), 
        "description": _("In the context of the HTML canvas element WebGL provides an API for 3D graphics in the browser."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/WebGL')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/WebGL')),
            (_('Khronos Spec'),      _('http://www.khronos.org/webgl/')),
        ),
    },
    { 
        "tag_name": "tech:websockets", 
        "title": _("WebSockets"), 
        "description": _("WebSockets is a technology that makes it possible to open an interactive  communication session between the user's browser and a server."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/WebSockets')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Web_Sockets')),
            (_('W3C Spec'),          _('http://dev.w3.org/html5/websockets/')),
        ),
    },
    { 
        "tag_name": "tech:webworkers", 
        "title": _("Web Workers"), 
        "description": _("Web Workers provide a simple means for web content to run scripts in background threads."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/En/Using_web_workers')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Web_Workers')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/workers/')),
        ),
    },
    { 
        "tag_name": "tech:xhr", 
        "title": _("XMLHttpRequest"), 
        "description": _("XMLHttpRequest (XHR) is used to send HTTP requests directly to a webserver and load the response data directly back into the script."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/En/XMLHttpRequest/Using_XMLHttpRequest')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/XMLHttpRequest')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/XMLHttpRequest/')),
        ),
    },
    { 
        "tag_name": "tech:multitouch", 
        "title": _("Multi-touch"), 
        "description": _("Track the movement of the user's finger on a touch screen, monitoring the raw touch events generated by the system."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en/DOM/Touch_events')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Multi-touch')),
            (_('W3C Spec'),          _('http://www.w3.org/2010/webevents/charter/')),
        ),
    },
)))

# HACK: For easier L10N, define license in code instead of as a DB model
DEMO_LICENSES = dict( (x['name'], x) for x in getattr(settings, 'DEMO_LICENSES', (
    { 
        'name': "mpl", 
        'title': _("MPL/GPL/LGPL"),
        'link': _('http://www.mozilla.org/MPL/'),
        'icon': '',
    },
    { 
        'name': "gpl", 
        'title': _("GPL"),
        'link': _('http://www.opensource.org/licenses/gpl-license.php'),
        'icon': '',
    },
    { 
        'name': "bsd", 
        'title': _("BSD"),
        'link': _('http://www.opensource.org/licenses/bsd-license.php'),
        'icon': '',
    },
    { 
        'name': "apache", 
        'title': _("Apache"),
        'link': _('http://www.apache.org/licenses/'),
        'icon': '',
    },
    { 
        'name': "publicdomain", 
        'title': _("Public Domain (where applicable by law)"),
        'link': _('http://creativecommons.org/publicdomain/zero/1.0/'),
        'icon': '',
    },
)))


def scale_image(img_upload, img_max_size):
    """Crop and scale an image file."""
    try:
        img = Image.open(img_upload)
    except IOError:
        return None

    src_width, src_height = img.size
    src_ratio = float(src_width) / float(src_height)
    dst_width, dst_height = img_max_size
    dst_ratio = float(dst_width) / float(dst_height)

    if dst_ratio < src_ratio:
        crop_height = src_height
        crop_width = crop_height * dst_ratio
        x_offset = int(float(src_width - crop_width) / 2)
        y_offset = 0
    else:
        crop_width = src_width
        crop_height = crop_width / dst_ratio
        x_offset = 0
        y_offset = int(float(src_height - crop_height) / 3)

    img = img.crop((x_offset, y_offset, 
        x_offset+int(crop_width), y_offset+int(crop_height)))
    img = img.resize((dst_width, dst_height), Image.ANTIALIAS)

    if img.mode != "RGB":
        img = img.convert("RGB")
    new_img = StringIO()
    img.save(new_img, "JPEG")
    img_data = new_img.getvalue()

    return ContentFile(img_data)

