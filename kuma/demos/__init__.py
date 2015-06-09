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

# For easier L10N, define tag descriptions in code instead of as a DB model.
#
# Copy that is not displayed is commented so that localizers do not waste time
# translating it.
#
# The following can be commented unless a trophy is shown for the contest:
# * short_dateline
# * tagline
#
# The following can be commented unless the contest is underway:
# * tab_copy
#
# Everything else is used somewhere.
TAG_DESCRIPTIONS = dict((x['tag_name'], x) for x in getattr(
    settings, 'TAG_DESCRIPTIONS', (
        {"tag_name": "challenge:none",
         "title": _("None"),
         "description": _("Removed from Derby")},
        {"tag_name": "challenge:2011:june",
         "title": _("June 2011 Dev Derby Challenge - CSS3 Animations"),
         "short_title": _("CSS3 Animations"),
         "dateline": _("June 2011"),
         "summary": _("CSS3 Animations let you change property values over time, to animate the appearance or position of elements, with no or minimal JavaScript, and with greater control than transitions."),
         "description": _("CSS3 Animations are a new feature of modern browsers like Firefox, which add even more flexibility and control to the style and experience of the Web. CSS3 Animations let you change property values over time with no or minimal JavaScript, and with greater control than CSS Transitions. Go beyond static properties to animate the appearance and positions of HTML elements. You can achieve these effects without Flash or Silverlight, to make creative dynamic interfaces and engaging animations with CSS3."),
         "learn_more": []},
        {"tag_name": "challenge:2011:july",
         "title": _("July 2011 Dev Derby Challenge - HTML5 <video>"),
         "short_title": _("HTML5 <video>"),
         "dateline": _("July 2011"),
         "summary": _("The HTML5 <video> element lets you embed and control video media directly in web pages, without resorting to plug-ins."),
         "description": _("The HTML5 <video> element lets you embed and control video media directly in web pages, without resorting to plug-ins."),
         "learn_more": []},
        {"tag_name": "challenge:2011:august",
         "title": _("August 2011 Dev Derby Challenge - History API"),
         "short_title": _("History API"),
         "dateline": _("August 2011"),
         "summary": _("The History API in modern browsers enables live changes to the document without breaking the back button and allows apps to be bookmarked."),
         "description": _("The History API in modern browsers enables live changes to the document without breaking the back button and allows apps to be bookmarked."),
         "learn_more": []},
        {"tag_name": "challenge:2011:september",
         "title": _("September 2011 Dev Derby Challenge - Geolocation"),
         "short_title": _("Geolocation"),
         "dateline": _("September 2011"),
         "summary": _("With Geolocation, you can get the user's physical location (with permission) and use it to enhance the browsing experience or enable advanced location-aware features."),
         "description": _("With Geolocation, you can get the user's physical location (with permission) and use it to enhance the browsing experience or enable advanced location-aware features."),
         "learn_more": []},
        {"tag_name": "challenge:2011:october",
         "title": _("October 2011 Dev Derby Challenge - CSS Media Queries"),
         "short_title": _("CSS Media Queries"),
         "dateline": _("October 2011"),
         "summary": _("CSS Media Queries allow Web developers to create responsive Web designs, tailoring the user experience for a range of screen sizes, including desktops, tablets, and mobiles."),
         "description": _("CSS Media Queries allow Web developers to create responsive Web designs, tailoring the user experience for a range of screen sizes, including desktops, tablets, and mobiles."),
         "learn_more": []},
        {"tag_name": "challenge:2011:november",
         "title": _("November 2011 Dev Derby Challenge - Canvas"),
         "short_title": _("Canvas"),
         "dateline": _("November 2011"),
         "summary": _("Canvas lets you paint the Web using JavaScript to render 2D shapes, bitmapped images, and advanced graphical effects.  Each <canvas> element provides a graphics context with its own state and methods that make it easy to control and draw in."),
         "description": _("Canvas lets you paint the Web using JavaScript to render 2D shapes, bitmapped images, and advanced graphical effects.  Each <canvas> element provides a graphics context with its own state and methods that make it easy to control and draw in."),
         "learn_more": []},
        {"tag_name": "challenge:2011:december",
         "title": _("December 2011 Dev Derby Challenge - IndexedDB"),
         "short_title": _("IndexedDB"),
         "dateline": _("December 2011"),
         "summary": _("IndexedDB lets web applications store significant amounts of structured data locally, for faster access, online or offline."),
         "description": _("IndexedDB lets web applications store significant amounts of structured data locally, for faster access, online or offline."),
         "learn_more": []},
        {"tag_name": "challenge:2012:january",
         "title": _("January 2012 Dev Derby Challenge - Orientation"),
         "short_title": _("Orientation"),
         "dateline": _("January 2012"),
         "summary": _("Orientation features in HTML5 access the motion and orientation data of devices with accelerometers."),
         "description": _("Orientation features in HTML5 access the motion and orientation data of devices with accelerometers."),
         "learn_more": []},
        {"tag_name": "challenge:2012:february",
         "title": _("February 2012 Dev Derby Challenge - Touch Events"),
         "short_title": _("Touch Events"),
         "dateline": _("February 2012"),
         "summary": _("Touch Events help you make websites and applications more engaging by responding appropriately when users interact with touch screens."),
         "description": _("Touch Events help you make websites and applications more engaging by responding appropriately when users interact with touch screens."),
         "learn_more": []},
        {"tag_name": "challenge:2012:march",
         "title": _("March 2012 Dev Derby Challenge - CSS 3D Transforms"),
         "short_title": _("CSS 3D Transforms"),
         "dateline": _("March 2012"),
         "summary": _("CSS 3D Transforms extends CSS Transforms to allow elements rendered by CSS to be transformed in three-dimensional space."),
         "description": _("CSS 3D Transforms extends CSS Transforms to allow elements rendered by CSS to be transformed in three-dimensional space."),
         "learn_more": []},
        {"tag_name": "challenge:2012:april",
         "title": _("April 2012 Dev Derby Challenge - Audio"),
         "short_title": _("Audio"),
         "dateline": _("April 2012"),
         "summary": _("The HTML5 audio element lets you embed sound in webpages without requiring your users to rely on plug-ins."),
         "description": _("The HTML5 audio element lets you embed sound in webpages without requiring your users to rely on plug-ins."),
         "learn_more": []},
        {"tag_name": "challenge:2012:may",
         "title": _("May 2012 Dev Derby Challenge - WebSockets API"),
         "short_title": _("WebSockets API"),
         "dateline": _("May 2012"),
         "summary": _("With the Websocket API and protocol, you can open a two-way channel between the browser and a server, for scalable and real-time data flow. No more server polling!"),
         "description": _("With the Websocket API and protocol, you can open a two-way channel between the browser and a server, for scalable and real-time data flow. No more server polling!"),
         "learn_more": []},
        {"tag_name": "challenge:2012:june",
         "title": _("June 2012 Dev Derby Challenge - WebGL"),
         "short_title": _("WebGL"),
         "dateline": _("June 2012"),
         "summary": _("WebGL brings the power of OpenGL, for creating interactive 3D graphics, to the Web, with no plug-ins required."),
         "description": _("WebGL brings the power of OpenGL, for creating interactive 3D graphics, to the Web, with no plug-ins required."),
         "learn_more": []},
        {"tag_name": "challenge:2012:july",
         "title": _("July 2012 Dev Derby Challenge - No JavaScript"),
         "short_title": _("No JavaScript"),
         "dateline": _("July 2012"),
         "summary": _("Creating rich user experiences for the Web has never been easier. Today's open Web standards put some of the most powerful features right at your fingertips. Animate pages with CSS, validate user input with HTML, and more. What else can you do without JavaScript?"),
         "description": _("Creating rich user experiences for the Web has never been easier. Today's open Web standards put some of the most powerful features right at your fingertips. Animate pages with CSS, validate user input with HTML, and more. What else can you do without JavaScript?"),
         "learn_more": []},
        {"tag_name": "challenge:2012:august",
         "title": _("August 2012 Dev Derby Challenge - Camera API"),
         "short_title": _("Camera API"),
         "dateline": _("August 2012"),
         "summary": _("The Camera API lets you access (with permission) the cameras of mobile devices. With the Camera API, users can easily take pictures and upload them to your web page."),
         "description": _("The Camera API lets you access (with permission) the cameras of mobile devices. With the Camera API, users can easily take pictures and upload them to your web page."),
         "learn_more": []},
        {"tag_name": "challenge:2012:september",
         "title": _("September 2012 Dev Derby Challenge - Geolocation II"),
         "short_title": _("Geolocation II"),
         "dateline": _("September 2012"),
         "summary": _("With Geolocation, you can get the user's physical location (with permission) and use it to enhance the browsing experience or enable advanced location-aware features."),
         "description": _("With Geolocation, you can get the user's physical location (with permission) and use it to enhance the browsing experience or enable advanced location-aware features."),
         "learn_more": []},
        {"tag_name": "challenge:2012:october",
         "title": _("October 2012 Dev Derby Challenge - CSS Media Queries II"),
         "short_title": _("CSS Media Queries II"),
         "dateline": _("October 2012"),
         "summary": _("CSS Media Queries are now a common tool for responsive, mobile-first web design. They are now even a W3C Recommendation! They can tell you a lot more about a display than just its width. What can you do with Media Queries?"),
         "description": _("CSS Media Queries are now a common tool for responsive, mobile-first web design. They are now even a W3C Recommendation! They can tell you a lot more about a display than just its width. What can you do with Media Queries?"),
         "learn_more": []},
        {"tag_name": "challenge:2012:november",
         "title": _("November 2012 Dev Derby Challenge - Fullscreen API"),
         "short_title": _("Fullscreen API"),
         "dateline": _("November 2012"),
         "summary": _("With the Fullscreen API, you can escape the confines of the browser window. You can even detect full screen state changes and style full screen pages specially. Talk about immersive!"),
         "description": _("With the Fullscreen API, you can escape the confines of the browser window. You can even detect full screen state changes and style full screen pages specially. Talk about immersive!"),
         "learn_more": []},
        {"tag_name": "challenge:2012:december",
         "title": _("December 2012 Dev Derby Challenge - Offline"),
         "short_title": _("Offline"),
         "dateline": _("December 2012"),
         "summary": _("With the maturing offline capabilities of the open Web, you can build apps that work with or without an Internet connection. With offline technologies, you can better support travelers and mobile users, improve performance, and more."),
         "description": _("With the maturing offline capabilities of the open Web, you can build apps that work with or without an Internet connection. With offline technologies, you can better support travelers and mobile users, improve performance, and more."),
         "learn_more": []},
        {"tag_name": "challenge:2013:january",
         "title": _("January 2013 Dev Derby Challenge - Drag and Drop"),
         "short_title": _("Drag and Drop"),
         "dateline": _("January 2013"),
         "summary": _("The Drag and Drop API brings an age-old interaction to the Web, making rich, natural, and familiar user experiences possible."),
         "description": _("The Drag and Drop API brings an age-old interaction to the Web, making rich, natural, and familiar user experiences possible."),
         "learn_more": []},
        {"tag_name": "challenge:2013:february",
         "title": _("February 2013 Dev Derby Challenge - Multi-touch"),
         "short_title": _("Multi-touch"),
         "dateline": _("February 2013"),
         "summary": _("The Touch Events API lets you track multiple touches at the same time on devices that support them. Build complex games, support pinch-to-zoom and more. By using multi-touch, your app can respond to all the interactions users have come to expect."),
         "description": _("The Touch Events API lets you track multiple touches at the same time on devices that support them. Build complex games, support pinch-to-zoom and more. By using multi-touch, your app can respond to all the interactions users have come to expect."),
         "learn_more": []},
        {"tag_name": "challenge:2013:march",
         "title": _("March 2013 Dev Derby Challenge - Mobile"),
         "short_title": _("Mobile"),
         "dateline": _("March 2013"),
         "summary": _("The mobile Web is becoming more important every day. This time, the only limit is your creativity. What amazing experiences can you build for users on the go?"),
         "description": _("The mobile Web is becoming more important every day. This time, the only limit is your creativity. What amazing experiences can you build for users on the go?"),
         "learn_more": []},
        {"tag_name": "challenge:2013:april",
         "title": _("April 2013 Dev Derby Challenge - Web Workers"),
         "short_title": _("Web Workers"),
         "dateline": _("April 2013"),
         "summary": _("Web Workers make it easy for you to run scripts in the background. By using Web Workers, you can create dazzling user interfaces that are not hindered by even the most computationally-intensive tasks."),
         "description": _("Web Workers make it easy for you to run scripts in the background. By using Web Workers, you can create dazzling user interfaces that are not hindered by even the most computationally-intensive tasks."),
         "learn_more": []},
        {"tag_name": "challenge:2013:may",
         "title": _("May 2013 Dev Derby Challenge - getUserMedia"),
         "short_title": _("getUserMedia"),
         "dateline": _("May 2013"),
         "short_dateline": _("May"),
         "tagline": _("Action!"),
         "summary": _("The getUserMedia function lets you access (with permission) the cameras and microphones of your users. No plugins needed! What can you do once you have this media? The possibilities are endless."),
         "description": _("The getUserMedia function lets you access (with permission) the cameras and microphones of your users. No plugins needed! What can you do once you have this media? The possibilities are endless."),
         "learn_more": []},
        {"tag_name": "challenge:2013:june",
         "title": _("June 2013 Dev Derby Challenge - WebGL II"),
         "short_title": _("WebGL II"),
         "dateline": _("June 2013"),
         "short_dateline": _("June"),
         "tagline": _("Twice the 3D!"),
         "summary": _("WebGL brings the power of OpenGL, for creating interactive 3D graphics, to the Web, with no plug-ins required."),
         "description": _("WebGL brings the power of OpenGL, for creating interactive 3D graphics, to the Web, with no plug-ins required."),
         "learn_more": []},
        {"tag_name": "challenge:2013:july",
         "title": _("July 2013 Dev Derby Challenge - File API"),
         "short_title": _("File API"),
         "dateline": _("July 2013"),
         "short_dateline": _("July"),
         "tagline": _("File found"),
         "summary": _("The File API lets you read the contents of files submitted by your users, making natural and familiar data operations possible."),
         "description": _("The File API lets you read the contents of files submitted by your users, making natural and familiar data operations possible."),
         "learn_more": []},

        {"tag_name": "tech:audio",
         "title": _("Audio"),
         "description": _("Mozilla's Audio Data API extends the current HTML5 API and allows web developers to read and write raw audio data."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Introducing_the_Audio_API_Extension')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/HTML5_audio')),
             (_('W3C Spec'), _('http://www.w3.org/TR/html5/video.html#audio')),
         )},
        {"tag_name": "tech:canvas",
         "title": _("Canvas"),
         "description": _("The HTML5 canvas element allows you to display scriptable renderings of 2D shapes and bitmap images."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/HTML/Canvas')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Canvas_element')),
             (_('W3C Spec'), _('http://www.w3.org/TR/html5/the-canvas-element.html')),
         )},
        {"tag_name": "tech:css3",
         "title": _("CSS3"),
         "description": _("Cascading Style Sheets level 3 (CSS3) provide serveral new features and properties to enhance the formatting and look of documents written in different kinds of markup languages like HTML or XML."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Web/CSS')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Cascading_Style_Sheets')),
             (_('W3C Spec'), _('http://www.w3.org/TR/css3-roadmap/')),
         )},
        {"tag_name": "tech:device",
         "title": _("Device"),
         "description": _("Media queries and orientation events let authors adjust their layout on hand-held devices such as mobile phones."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/WebAPI/Detecting_device_orientation')),
             (_('W3C Spec'), _('http://www.w3.org/TR/css3-mediaqueries/')),
         )},
        {"tag_name": "tech:files",
         "title": _("Files"),
         "description": _("The File API allows web developers to use file objects in web applications, as well as selecting and accessing their data."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/using_files_from_web_applications')),
             (_('W3C Spec'), _('http://www.w3.org/TR/FileAPI/')),
         )},
        {"tag_name": "tech:fonts",
         "title": _("Fonts & Type"),
         "description": _("The CSS3-Font specification contains enhanced features for fonts and typography like  embedding own fonts via @font-face or controlling OpenType font features directly via CSS."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Web/CSS/@font-face')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Web_typography')),
             (_('W3C Spec'), _('http://www.w3.org/TR/css3-fonts/')),
         )},
        {"tag_name": "tech:forms",
         "title": _("Forms"),
         "description": _("Form elements and attributes in HTML5 provide a greater degree of semantic mark-up than HTML4 and remove a great deal of the need for tedious scripting and styling that was required in HTML4."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Web/HTML/Forms_in_HTML')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/HTML_forms')),
             (_('W3C Spec'), _('http://www.w3.org/TR/html5/forms.html')),
         )},
        {"tag_name": "tech:geolocation",
         "title": _("Geolocation"),
         "description": _("The Geolocation API allows web applications to access the user's geographical location."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/WebAPI/Using_geolocation')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/W3C_Geolocation_API')),
             (_('W3C Spec'), _('http://dev.w3.org/geo/api/spec-source.html')),
         )},
        {"tag_name": "tech:javascript",
         "title": _("JavaScript"),
         "description": _("JavaScript is a lightweight, object-oriented programming language, commonly used for scripting interactive behavior on web pages and in web applications."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Web/JavaScript')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/JavaScript')),
             (_('ECMA Spec'), _('http://www.ecma-international.org/publications/standards/Ecma-262.htm')),
         )},
        {"tag_name": "tech:html5",
         "title": _("HTML5"),
         "description": _("HTML5 is the newest version of the HTML standard, currently under development."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/HTML5')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Html5')),
             (_('W3C Spec'), _('http://dev.w3.org/html5/spec/Overview.html')),
         )},
        {"tag_name": "tech:indexeddb",
         "title": _("IndexedDB"),
         "description": _("IndexedDB is an API for client-side storage of significant amounts of structured data and for high performance searches on this data using indexes. "),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/IndexedDB')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/IndexedDB')),
             (_('W3C Spec'), _('http://www.w3.org/TR/IndexedDB/')),
         )},
        {"tag_name": "tech:dragndrop",
         "title": _("Drag and Drop"),
         "description": _("Drag and Drop features allow the user to move elements on the screen using the mouse pointer."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/DragDrop/Drag_and_Drop')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Drag-and-drop')),
             (_('W3C Spec'), _('http://www.w3.org/TR/html5/dnd.html')),
         )},
        {"tag_name": "tech:mobile",
         "title": _("Mobile"),
         "description": _("Firefox Mobile brings the true Web experience to mobile phones and other non-PC devices."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Mozilla/Mobile')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Mobile_web')),
             (_('W3C Spec'), _('http://www.w3.org/Mobile/')),
         )},
        {"tag_name": "tech:offlinesupport",
         "title": _("Offline Support"),
         "description": _("Offline caching of web applications' resources using the application cache and local storage."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Web/Guide/DOM/Storage#localStorage')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Web_Storage')),
             (_('W3C Spec'), _('http://dev.w3.org/html5/webstorage/')),
         )},
        {"tag_name": "tech:svg",
         "title": _("SVG"),
         "description": _("Scalable Vector Graphics (SVG) is an XML based language for describing two-dimensional vector graphics."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Web/SVG')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Scalable_Vector_Graphics')),
             (_('W3C Spec'), _('http://www.w3.org/TR/SVG11/')),
         )},
        {"tag_name": "tech:video",
         "title": _("Video"),
         "description": _("The HTML5 video element provides integrated support for playing video media without requiring plug-ins."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Web/HTML/Using_HTML5_audio_and_video')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/HTML5_video')),
             (_('W3C Spec'), _('http://www.w3.org/TR/html5/video.html')),
         )},
        {"tag_name": "tech:webgl",
         "title": _("WebGL"),
         "description": _("In the context of the HTML canvas element WebGL provides an API for 3D graphics in the browser."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Web/WebGL')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/WebGL')),
             (_('Khronos Spec'), _('http://www.khronos.org/webgl/')),
         )},
        {"tag_name": "tech:websockets",
         "title": _("WebSockets"),
         "description": _("WebSockets is a technology that makes it possible to open an interactive  communication session between the user's browser and a server."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/WebSockets')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Web_Sockets')),
             (_('W3C Spec'), _('http://dev.w3.org/html5/websockets/')),
         )},
        {"tag_name": "tech:webworkers",
         "title": _("Web Workers"),
         "description": _("Web Workers provide a simple means for web content to run scripts in background threads."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Web/Guide/Performance/Using_web_workers')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Web_Workers')),
             (_('W3C Spec'), _('http://www.w3.org/TR/workers/')),
         )},
        {"tag_name": "tech:xhr",
         "title": _("XMLHttpRequest"),
         "description": _("XMLHttpRequest (XHR) is used to send HTTP requests directly to a webserver and load the response data directly back into the script."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest/Using_XMLHttpRequest')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/XMLHttpRequest')),
             (_('W3C Spec'), _('http://www.w3.org/TR/XMLHttpRequest/')),
         )},
        {"tag_name": "tech:multitouch",
         "title": _("Multi-touch"),
         "description": _("Track the movement of the user's finger on a touch screen, monitoring the raw touch events generated by the system."),
         "learn_more": (
             (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Web/Guide/DOM/Events/Touch_events')),
             (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Multi-touch')),
             (_('W3C Spec'), _('http://www.w3.org/2010/webevents/charter/')),
         )})))


DEFAULT_LICENSES = (
    {'name': 'mpl',
     'title': _('MPL/GPL/LGPL'),
     'link': _('http://www.mozilla.org/MPL/')},
    {'name': 'gpl',
     'title': _('GPL'),
     'link': _('http://www.opensource.org/licenses/gpl-license.php')},
    {'name': 'bsd',
     'title': _('BSD'),
     'link': _('http://www.opensource.org/licenses/bsd-license.php')},
    {'name': 'apache',
     'title': _('Apache'),
     'link': _('http://www.apache.org/licenses/')},
    {'name': 'publicdomain',
     'title': _('Public Domain (where applicable by law)'),
     'link': _('http://creativecommons.org/publicdomain/zero/1.0/')},
)


DEMO_LICENSES = dict(
    (license['name'], license)
    for license in getattr(settings, 'DEMO_LICENSES', DEFAULT_LICENSES))


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

    img = img.crop(
        (x_offset, y_offset,
         x_offset + int(crop_width), y_offset + int(crop_height)))
    img = img.resize((dst_width, dst_height), Image.ANTIALIAS)

    if img.mode != "RGB":
        img = img.convert("RGB")
    new_img = StringIO()
    img.save(new_img, "JPEG")
    img_data = new_img.getvalue()

    return ContentFile(img_data)
