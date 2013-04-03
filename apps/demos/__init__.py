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

# For easier L10N, define tag descriptions in code instead of as a DB model
TAG_DESCRIPTIONS = dict((x['tag_name'], x) for x in getattr(
    settings, 'TAG_DESCRIPTIONS', (
    {
        "tag_name": "challenge:none",
        "title": _("None"),
        "description": _("Removed from Derby"),
    },
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
        "summary": _("Canvas lets you paint the Web using JavaScript to render 2D shapes, bitmapped images, and advanced graphical effects.  Each <canvas> element provides a graphics context with its own state and methods that make it easy to control and draw in."),
        "description": _("Canvas lets you paint the Web using JavaScript to render 2D shapes, bitmapped images, and advanced graphical effects.  Each <canvas> element provides a graphics context with its own state and methods that make it easy to control and draw in."),
        "learn_more": [],
        "tab_copy": _("""
        <p>The HTML5 Canvas element and API let you paint the Web using JavaScript to render and animate 2-D shapes, bitmapped images, and advanced graphical effects. But that's just the beginning. Because it's done with JavaScript, every line, shape or pixel you draw can interact with the rest of the page, other JavaScript APIs, other data, and of course, the user. If you can dream it, you can draw it.</p>"""),
    },
    {
        "tag_name": "challenge:2011:december",
        "title": _("December 2011 Dev Derby Challenge - IndexedDB"),
        "short_title": _("IndexedDB"),
        "dateline": _("December 2011"),
        "short_dateline": _("December"),
        "tagline": _("Take your data with you."),
        "summary": _("IndexedDB lets web applications store significant amounts of structured data locally, for faster access, online or offline."),
        "description": _("IndexedDB lets web applications store significant amounts of structured data locally, for faster access, online or offline."),
        "learn_more": [],
        "tab_copy": _("IndexedDB lets Web applications store significant amounts of structured data locally, for faster access, online or offline. You can store data using key-value pairs, where the values are whole objects, without having to serialize them (as you do with document-oriented databases) or coerce them into a relational structure (as with relational databases). "),
    },
    {
        "tag_name": "challenge:2012:january",
        "title": _("January 2012 Dev Derby Challenge - Orientation"),
        "short_title": _("Orientation"),
        "dateline": _("January 2012"),
        "short_dateline": _("January"),
        "tagline": _("Which way is up?"),
        "summary": _("Orientation features in HTML5 access the motion and orientation data of devices with accelerometers."),
        "description": _("Orientation features in HTML5 access the motion and orientation data of devices with accelerometers."),
        "learn_more": [],
        "tab_copy": _("Orientation features in HTML5 enable Web developers to access the motion and orientation data of devices with accelerometers, to create more engaging and interactive Web experiences."),
    },
    {
        "tag_name": "challenge:2012:february",
        "title": _("February 2012 Dev Derby Challenge - Touch Events"),
        "short_title": _("Touch Events"),
        "dateline": _("February 2012"),
        "short_dateline": _("February"),
        "tagline": _("Touch me."),
        "summary": _("Touch Events help you make websites and applications more engaging by responding appropriately when users interact with touch screens."),
        "description": _("Touch Events help you make websites and applications more engaging by responding appropriately when users interact with touch screens."),
        "learn_more": [],
        "tab_copy": _("A user touching a touch screen is very different from a user clicking a mouse button. Use touch events to make sure that your Web application responds to touch screen interactions in ways that users expect."),
    },
    {
        "tag_name": "challenge:2012:march",
        "title": _("March 2012 Dev Derby Challenge - CSS 3D Transforms"),
        "short_title": _("CSS 3D Transforms"),
        "dateline": _("March 2012"),
        "short_dateline": _("March"),
        "tagline": _("Now with 50% more D!"),
        "summary": _("CSS 3D Transforms extends CSS Transforms to allow elements rendered by CSS to be transformed in three-dimensional space."),
        "description": _("CSS 3D Transforms extends CSS Transforms to allow elements rendered by CSS to be transformed in three-dimensional space."),
        "learn_more": [],
        "tab_copy": _("Three-D interfaces have always been a fascination for as long as we have used computers. CSS 3D transforms allows you to add depth to effects and makes it easier to add more content into the same screen space by stacking it. By moving and rotating content in the X, Y and Z axis you can create beautiful transitions and interfaces without having to learn a new language."),
    },
    {
        "tag_name": "challenge:2012:april",
        "title": _("April 2012 Dev Derby Challenge - Audio"),
        "short_title": _("Audio"),
        "dateline": _("April 2012"),
        "short_dateline": _("April"),
        "tagline": _("Can you hear me now?"),
        "summary": _("The HTML5 audio element lets you embed sound in webpages without requiring your users to rely on plug-ins."),
        "description": _("The HTML5 audio element lets you embed sound in webpages without requiring your users to rely on plug-ins."),
        "learn_more": [],
        "tab_copy": _("<p>The <a href=\"/en-US/docs/HTML/Element/audio\">HTML5 &lt;audio&gt;</a> element lets you embed sound in Web pages. More importantly, it lets you do so without requiring your users to rely on plug-ins. This means sound for everyone, everywhere, in the most open way possible. In particular, you can play sounds in games with <a href=\"http://robert.ocallahan.org/2011/11/latency-of-html5-sounds.html\">very low latency</a>, making for a responsive, immersive game experience.</p><p>What else can you do with the audio element? Show us by submitting to the Dev Derby today.</p>"),
    },
    {
        "tag_name": "challenge:2012:may",
        "title": _("May 2012 Dev Derby Challenge - WebSockets API"),
        "short_title": _("WebSockets API"),
        "dateline": _("May 2012"),
        "short_dateline": _("May"),
        "tagline": _("send() us your best"),
        "summary": _("With the Websocket API and protocol, you can open a two-way channel between the browser and a server, for scalable and real-time data flow. No more server polling!"),
        "description": _("With the Websocket API and protocol, you can open a two-way channel between the browser and a server, for scalable and real-time data flow. No more server polling!"),
        "learn_more": [],
        "tab_copy": _("""<p>With the <a href="/en-US/docs/WebSockets">Websocket API and protocol</a>, you can open a two-way communication channel between the browser and a server. This lets you send messages to the server and receive event-driven responses in real time, all without server polling. Websockets are simple, scalable, and future-proof. <a href="http://www.websocket.org/">Websocket.org</a> even argues that Websockets are the "next evolutionary step in web communication."</p>
<p>Not excited yet? This is about more than just sending messages&mdash;it's about highly interactive experiences. Last month, Little Workshop and Mozilla collaborated to create <a href="https://hacks.mozilla.org/2012/03/browserquest/">BrowserQuest</a>, a multiplayer online game that uses Websockets at its core. As if that weren't enough, Mozilla's very own Rob Hawkes created <a href="http://rawkets.com/">Rawkets</a>, a multiplayer space shooter that also uses Websockets.</p>
<p>Of course, you can't do much with Websockets unless you have a server to communicate with. Thankfully, there are many free Websockets servers available on the web, such as <a href="http://www.heroku.com/">Heroku</a> and <a href="http://nodejitsu.com/#/">Nodejitsu</a>. If you prefer, you could even use your own Websockets server.</p>
<p>Setting up a Websockets demo is more involved than setting up a static demo, but we know you can do it. As long as you keep these <a href="https://hacks.mozilla.org/2012/05/may-dev-derby-show-us-what-you-can-do-with-websockets/#may-derby-setup">three simple rules</a> in mind, everything should work flawlessly.</p>
<p>What can you create with the Websocket API and protocol? The next BrowserQuest? A better Rawkets? Show the world this month in the May Dev Derby!</p>"""),
    },
    {
        "tag_name": "challenge:2012:june",
        "title": _("June 2012 Dev Derby Challenge - WebGL"),
        "short_title": _("WebGL"),
        "dateline": _("June 2012"),
        "short_dateline": _("June"),
        "tagline": _("The Web: Now in amazing 3D!"),
        "summary": _("WebGL brings the power of OpenGL, for creating interactive 3D graphics, to the Web, with no plug-ins required."),
        "description": _("WebGL brings the power of OpenGL, for creating interactive 3D graphics, to the Web, with no plug-ins required."),
        "learn_more": [],
        "tab_copy": _("""<p>WebGL brings the power of OpenGL to the Web. Using WebGL, you can create interactive 3D graphics that work directly in modern browsers without plug-ins.
<p>Using WebGL is easier if you already have experience with graphics programming, but don't let that hold you back. <a href="http://learningwebgl.com/blog/?page_id=1217">Learning WebGL</a> provides a great set of tutorials for newcomers and the MDN offers <a href="/en-US/docs/WebGL">WebGL articles</a> that make a great next step. While you're working, you might also appreciate <a href="http://webglplayground.net/">WebGL Playground</a>, a handy tool that lets you edit your creations and see the results in real time.</p>
<p>Best of all, you have the power of the open-source community on your side. Be sure to consider the <a href="http://dev.opera.com/articles/view/an-introduction-to-webgl/#webgllib">many JavaScript libraries</a> that make writing WebGL animations even easier.</p>
<p>What can you do with WebGL? Show us this month in the June Dev Derby!</p>"""),
    },
    {
        "tag_name": "challenge:2012:july",
        "title": _("July 2012 Dev Derby Challenge - No JavaScript"),
        "short_title": _("No JavaScript"),
        "dateline": _("July 2012"),
        "short_dateline": _("July"),
        "tagline": _("Code with no.js!"),
        "summary": _("Creating rich user experiences for the Web has never been easier. Today's open Web standards put some of the most powerful features right at your fingertips. Animate pages with CSS, validate user input with HTML, and more. What else can you do without JavaScript?"),
        "description": _("Creating rich user experiences for the Web has never been easier. Today's open Web standards put some of the most powerful features right at your fingertips. Animate pages with CSS, validate user input with HTML, and more. What else can you do without JavaScript?"),
        "learn_more": [],
        "tab_copy": _("""<p>Who needs JavaScript? The expanding capabilities of HTML and CSS make it easier than ever to create rich user experiences for the Web. Mark Pilgrim captures this in <cite><a href="http://diveintohtml5.info/index.html">Dive into HTML5</a></cite> when he advises, "Scripting is here to stay, but should be avoided where more convenient declarative markup can be used." Today, declarative markup can be used to accomplish more than ever.</p>
<p>Dynamically adapt to different screen sizes using CSS <a href="https://developer.mozilla.org/en-US/docs/CSS/Media_queries">media queries</a>. Make a page come alive with CSS <a href="https://developer.mozilla.org/en-US/docs/CSS/Using_CSS_transitions">transitions</a> and <a href="https://developer.mozilla.org/en-US/docs/CSS/Using_CSS_animations">animations</a>. Create eye-popping graphics and animations with <a href="https://developer.mozilla.org/en-US/docs/CSS/Using_CSS_transforms#3D_specific_CSS_properties">3D transforms</a>. Warn users about invalid input with HTML <a href="https://developer.mozilla.org/en-US/docs/HTML/Forms_in_HTML#section_8">form validation</a>. Provide rich media with graceful fallbacks using HTML5 <a href="https://developer.mozilla.org/en-US/docs/Using_HTML5_audio_and_video">video and audio</a>. The open Web lets you do all of this and more, all without a single line of JavaScript.</p>
<p>So hold the JavaScript and show us what you can do this month in the July Dev Derby!</p>"""),
    },
    {
        "tag_name": "challenge:2012:august",
        "title": _("August 2012 Dev Derby Challenge - Camera API"),
        "short_title": _("Camera API"),
        "dateline": _("August 2012"),
        "short_dateline": _("August"),
        "tagline": _("Say cheese!"),
        "summary": _("The Camera API lets you access (with permission) the cameras of mobile devices. With the Camera API, users can easily take pictures and upload them to your web page."),
        "description": _("The Camera API lets you access (with permission) the cameras of mobile devices. With the Camera API, users can easily take pictures and upload them to your web page."),
        "learn_more": [],
        "tab_copy": _("""<p>The <a href="https://hacks.mozilla.org/2012/04/taking-pictures-with-the-camera-api-part-of-webapi/">Camera API</a> lets you access the cameras of mobile devices (with the user's permission, of course!). By using the Camera API, you can help users take photos (or retrieve existing ones) and upload them to a web page easily. No <em>Browse</em> button and no digging through obscure file names. This is totally seamless photo sharing.</p>
<p>The Camera API was born out of Mozilla's <a href="https://wiki.mozilla.org/WebAPI">WebAPI</a> project, but has already gained support across browsers. Users of <a href="https://www.mozilla.org/firefox/mobile/features/">Firefox for Android</a>, Chrome for Android, and recent versions of the stock Android Browser can already reap the benefits.</p>
<p>Mozilla's Robert Nyman has written a great article on <a href="https://hacks.mozilla.org/2012/04/taking-pictures-with-the-camera-api-part-of-webapi/">using the Camera API</a> and a <a href="http://robnyman.github.com/camera-api/">live demo</a> of it. Unfortunately, little other creative work has been done with this powerful technology. That's where you come in. What can you do with the Camera API? Show us this month in the August Dev Derby!</p>"""),
    },
    {
        "tag_name": "challenge:2012:september",
        "title": _("September 2012 Dev Derby Challenge - Geolocation II"),
        "short_title": _("Geolocation II"),
        "dateline": _("September 2012"),
        "short_dateline": _("September"),
        "tagline": _("Wish you were here!"),
        "summary": _("With Geolocation, you can get the user's physical location (with permission) and use it to enhance the browsing experience or enable advanced location-aware features."),
        "description": _("With Geolocation, you can get the user's physical location (with permission) and use it to enhance the browsing experience or enable advanced location-aware features."),
        "learn_more": [],
        "tab_copy": _("""<p>The Geolocation API lets you determine the location and movement of a user. What can you do with this information? Maps, social networking, games &mdash; the possibilities are endless. Looking for inspiration? Just take a look at some of the amazing things created for our <a href="https://developer.mozilla.org/en-US/demos/devderby/2011/september">first Geolocation Derby</a>.</p>
<p>Anyone can learn to use the Geolocation API, especially considering how much documentation we already have on the topic. Beginners might like <a href="https://hacks.mozilla.org/2011/09/where-on-earth-this-months-developer-derby-is-all-about-geolocation/">this blog post</a> from our very own Christian Heilmann (complete with an interactive code sample), and experts might like the <a href="https://developer.mozilla.org/en-US/docs/Using_geolocation">even more detailed documentation</a> available on the MDN.</p>
<p>The best part? You don't need to learn much to start using Geolocation on mobile devices right now. No Java, no Objective-C, no native SDKs. Just the web. And you already know how to use that, right?</p>"""),
    },
    {
        "tag_name": "challenge:2012:october",
        "title": _("October 2012 Dev Derby Challenge - CSS Media Queries II"),
        "short_title": _("CSS Media Queries II"),
        "dateline": _("October 2012"),
        "short_dateline": _("October"),
        "tagline": _("Size still matters"),
        "summary": _("CSS Media Queries are now a common tool for responsive, mobile-first web design. They are now even a W3C Recommendation! They can tell you a lot more about a display than just its width. What can you do with Media Queries?"),
        "description": _("CSS Media Queries are now a common tool for responsive, mobile-first web design. They are now even a W3C Recommendation! They can tell you a lot more about a display than just its width. What can you do with Media Queries?"),
        "learn_more": [],
        "tab_copy": _("""<p>CSS Media Queries have come a long way in the last year. Now a <a href="http://www.w3.org/TR/css3-mediaqueries/">W3C Recommendation</a>, media queries help you support the ever-expanding variety of screen sizes and resolutions in use today. Smart phones and feature phones, tablets and e-book readers, short screens, tall screens, and super-high-resolution screens -- the Web is growing, shrinking, and changing every day.</p>
<p>Building a Web app that works well across this spectrum can seem daunting, but we have you covered. Take a look at this <a href="http://css-tricks.com/css-media-queries/">introduction</a> from former Derby judge Chris Coyier and be sure to head over to the MDN for <a href="https://developer.mozilla.org/en-US/docs/CSS/Media_queries">more depth and more up-to-date information</a> after that. Need help testing your creation? The new <a href="https://developer.mozilla.org/en-US/docs/Tools/Responsive_Design_View">Responsive Design View</a> of Firefox Developer Tools makes debugging responsive web designs fast, easy, and fun.</p>
<p>Some <a href="https://developer.mozilla.org/en-US/demos/devderby/2011/october">great demos</a> were shared in our last Derby on this topic. What can you do with CSS Media Queries?</p>"""),
    },
    {
        "tag_name": "challenge:2012:november",
        "title": _("November 2012 Dev Derby Challenge - Fullscreen API"),
        "short_title": _("Fullscreen API"),
        "dateline": _("November 2012"),
        "short_dateline": _("November"),
        "tagline": _("Know no bounds"),
        "summary": _("With the Fullscreen API, you can escape the confines of the browser window. You can even detect full screen state changes and style full screen pages specially. Talk about immersive!"),
        "description": _("With the Fullscreen API, you can escape the confines of the browser window. You can even detect full screen state changes and style full screen pages specially. Talk about immersive!"),
        "learn_more": [],
        "tab_copy": _("""<p>The Fullscreen API lets you make your Web application&mdash;or just part of it&mdash;front and center, free from the toolbars and the menus that usually get in the way. But this is about more than just real estate. The Fullscreen API also also helps you detect when users toggle fullscreen mode and even style your content according to those changes. The possibilities really are endless.</p>
<p>This important new technology has already been put to good use in desktop applications like <a href="https://developer.mozilla.org/en-US/demos/detail/bananabread">BananaBread</a>, but what about mobile? As our very own Rob Hawkes and Christian Heilmann explain in a recent talk, the Fullscreen API can be used to <a href="https://www.youtube.com/watch?v=seYKzIMRvns#t=28m40s">build mobile apps that feel truly native</a>. Your users may not even know the difference. And because Firefox OS and Firefox for Android already support the Fullscreen API, you can begin using it right now.</p>
<p>New to all this? No problem. As always, we have you covered with some of the best documentation out there. Beginners might like the <a href="https://hacks.mozilla.org/2012/01/using-the-fullscreen-api-in-web-browsers/">introduction</a> we shared on the Mozilla Hacks blog earlier this year, and those looking for more information will probably appreciate the <a href="https://developer.mozilla.org/en-US/docs/DOM/Using_fullscreen_mode">additional depth</a> provided on Mozilla Developer Network.</p>
<p>As web developers, we often talk about building engaging experiences for our users. Doing so has never been more possible. What can you do with the Fullscreen API?</p>"""),
    },
    {
        "tag_name": "challenge:2012:december",
        "title": _("December 2012 Dev Derby Challenge - Offline"),
        "short_title": _("Offline"),
        "dateline": _("December 2012"),
        "short_dateline": _("December"),
        "tagline": _("Unplug"),
        "summary": _("With the maturing offline capabilities of the open Web, you can build apps that work with or without an Internet connection. With offline technologies, you can better support travelers and mobile users, improve performance, and more."),
        "description": _("With the maturing offline capabilities of the open Web, you can build apps that work with or without an Internet connection. With offline technologies, you can better support travelers and mobile users, improve performance, and more."),
        "learn_more": [],
        "tab_copy": _("""<p>Want to learn how to build apps? You've come to the right place. The Mozilla Dev Derby is a monthly Web development contest open to anyone willing to learn. No experience necessary! The Dev Derby provides a different challenge every month. This month, we want to see if you can create apps that work without an internet connection.</p>
<p>Building apps that work offline has never been easier. With modern Web technologies, you can build amazing offline apps without writing a single line of native code. Support travelers without learning how to build Android apps, improve performance for mobile users without diving deep into iPhone development&mdash;thanks to the Web, you can do all of this and more using only JavaScript, HTML, CSS and other technologies that are easy to learn and use.</p>
<p>Need help getting started? No problem. The Mozilla Developer Network (MDN) has you covered with <a href="https://developer.mozilla.org/en-US/">some of the best documentation out there</a>. Beginners should appreciate our <a href="https://developer.mozilla.org/en-US/learn">comprehensive documentation on the basics</a> and experts will love the thousands of other articles we provide. When you're ready to learn about offline apps in particular, take a look at Chris Heilmann's <a href="https://hacks.mozilla.org/2012/03/there-is-no-simple-solution-for-local-storage/">excellent article on where things stand</a>. The options can seem overwhelming&mdash;localStorage, IndexedDB, WebSQL, everCookie and more. Which tool is best for the job? Naturally, that depends on what the job is. The Web development community needs examples and patterns for which storage solutions to apply in which kinds of situations.</p>
<p>That's where you come in. Can you build great apps that are also snappy? Is code simplicity or the size of your audience more important? We often describe the Dev Derby as a platform for pushing the Web forward. Never has this goal been so within reach.</p>
<p>Predict the future by inventing it. Show the world what you think offline apps should look like by submitting one of your own to the December Dev Derby.</p>"""),
    },
    {
        "tag_name": "challenge:2013:january",
        "title": _("January 2013 Dev Derby Challenge - Drag and Drop"),
        "short_title": _("Drag and Drop"),
        "dateline": _("January 2013"),
        "short_dateline": _("January"),
        "tagline": _("Drop demos here"),
        "summary": _("The Drag and Drop API brings an age-old interaction to the Web, making rich, natural, and familiar user experiences possible."),
        "description": _("The Drag and Drop API brings an age-old interaction to the Web, making rich, natural, and familiar user experiences possible."),
        "learn_more": [],
        "tab_copy": _("""<p>The Mozilla Dev Derby is a monthly Web development contest open to anyone willing to learn. No experience necessary! This month, we want to see if you can build Web apps that support drag and drop interaction. Simple games, intuitive shopping carts, easier file uploads&mdash;the possibilities are endless.</p>
<p>Need help getting started? No problem. The <a href="https://developer.mozilla.org/">Mozilla Developer Network</a> (MDN) has you covered with some of the best documentation out there. Beginners will appreciate our <a href="https://developer.mozilla.org/learn">comprehensive documentation on the basics</a>, and more seasoned web developers should love the thousands of other articles provided. When you're ready to get started on your contest entry, take a look at the <a href="https://developer.mozilla.org/docs/DragDrop/Drag_and_Drop">drag and drop documentation</a> in particular. Need some examples? Check out this <a href="http://html5demos.com/drag">simple demo</a> and the <a href="https://developer.mozilla.org/demos/tag/tech:dragndrop">many more demos</a> available on the Mozilla Demo Studio.</p>
<p>There is a lot to learn, but you don't need to be an expert to create something great. What can you do with drag and drop?</p>"""),
    },
    {
        "tag_name": "challenge:2013:february",
        "title": _("February 2013 Dev Derby Challenge - Multi-touch"),
        "short_title": _("Multi-touch"),
        "dateline": _("February 2013"),
        "short_dateline": _("February"),
        "tagline": _("Do more with less"),
        "summary": _("The Touch Events API lets you track multiple touches at the same time on devices that support them. Build complex games, support pinch-to-zoom and more. By using multi-touch, your app can respond to all the interactions users have come to expect."),
        "description": _("The Touch Events API lets you track multiple touches at the same time on devices that support them. Build complex games, support pinch-to-zoom and more. By using multi-touch, your app can respond to all the interactions users have come to expect."),
        "learn_more": [],
        "tab_copy": _("""<p>The Mozilla Dev Derby is a monthly Web development contest open to anyone willing to learn. This month, we want to see what you can do with multi-touch interaction. Games, photo galleries, drawing tools and more. With multi-touch, you can build amazing Web experiences that respond to all of the gestures users have come to expect on mobile. Best of all, the experiences you build will work right out of the box on <a href="https://market.android.com/details?id=org.mozilla.firefox">Firefox for Android</a>, <a href="http://www.mozilla.org/en-US/firefoxos/">Firefox OS</a> and many other mobile platforms. No native code needed!</p>
<p>Need help getting started? No problem. The <a href="https://developer.mozilla.org/en-US/">Mozilla Developer Network (MDN)</a> has you covered with some of the best documentation out there. Beginners will appreciate our <a href="https://developer.mozilla.org/en-US/learn/">comprehensive guide on the basics</a> and more experienced web developers should love the thousands of other articles provided. When you're ready to learn about multi-touch in particular, take a look at our <a href="https://developer.mozilla.org/en-US/docs/DOM/Touch_events">very thorough Touch Events documentation</a>. Need some examples? Check out <a href="https://developer.mozilla.org/en-US/demos/detail/the-face-builder">The Face Builder</a> and the <a href="https://developer.mozilla.org/en-US/demos/tag/tech:multitouch">many other multi-touch demos</a> hosted on the Mozilla Demo Studio.</p>
<p>There is a lot to learn, but you don't need to be an expert to create something great. What can you do with multi-touch?</p>"""),
    },
    {
        "tag_name": "challenge:2013:march",
        "title": _("March 2013 Dev Derby Challenge - Mobile"),
        "short_title": _("Mobile"),
        "dateline": _("March 2013"),
        "short_dateline": _("March"),
        "tagline": _("On the go"),
        "summary": _("The mobile Web is becoming more important every day. This time, the only limit is your creativity. What amazing experiences can you build for users on the go?"),
        "description": _("The mobile Web is becoming more important every day. This time, the only limit is your creativity. What amazing experiences can you build for users on the go?"),
        "learn_more": [],
        "tab_copy": _("""<p>The Mozilla Dev Derby is a monthly Web development contest open to anyone willing to learn. This month, we want to see what amazing experiences you can create for mobile users. The only limit is your creativity.</p>
<p>Need help getting started? No problem. The Mozilla Developer Network (MDN) has you covered with some of the best documentation out there. Beginners will appreciate our <a href="https://developer.mozilla.org/en-US/learn">comprehensive guide on the basics</a> and more experienced Web developers should appreciate the thousands of other articles provided. When you're ready to tackle mobile in particular, take a look at our <a href="https://developer.mozilla.org/en-US/docs/Mobile/Mobile_Web_Development">detailed Mobile Web Development guide</a>. Need some examples? Check out the many <a href="https://developer.mozilla.org/en-US/demos/tag/tech:mobile">mobile-optimized demos</a> already available on the Demo Studio.</p>
<p>It may seem like there's a lot to learn, but you don't need to be an expert to create something great. What can you do with the mobile Web?</p>"""),
    },
    {
        "tag_name": "challenge:2013:april",
        "title": _("April 2013 Dev Derby Challenge - Web Workers"),
        "short_title": _("Web Workers"),
        "dateline": _("April 2013"),
        "short_dateline": _("April"),
        "tagline": _("Work smart"),
        "summary": _("Web Workers make it easy for you to run scripts in the background. By using Web Workers, you can create dazzling user interfaces that are not hindered by even the most computationally-intensive tasks."),
        "description": _("Web Workers make it easy for you to run scripts in the background. By using Web Workers, you can create dazzling user interfaces that are not hindered by even the most computationally-intensive tasks."),
        "learn_more": [],
        "tab_copy": _("""<p>The Mozilla Dev Derby is a monthly Web development contest open to anyone willing to learn. This month, we want to see what you can do with web workers. Web workers let you run scripts in the background, making even the most computationally-intensive applications possible.</p>
<p>Need help getting started? No problem. The <a href="https://developer.mozilla.org/en-US/">Mozilla Developer Network (MDN)</a> has you covered with some of the best documentation out there. Beginners will appreciate our <a href="https://developer.mozilla.org/en-US/learn">comprehensive guide on the basics</a> and more experienced Web developers should appreciate the thousands of other articles provided. When you're ready to tackle web workers in particular, take a look at our <a href="https://developer.mozilla.org/en-US/docs/DOM/Using_web_workers">detailed web workers guide</a>. Need some examples? The Demo Studio already has a handful of <a href="https://developer.mozilla.org/en-US/demos/tag/tech:webworkers">web worker demos</a> to learn from.</p>
<p>It may seem like a lot, but you don't need to be an expert to create something great. What can you do with web workers?</p>"""),
    },
    {
        "tag_name": "challenge:2013:may",
        "title": _("May 2013 Dev Derby Challenge - getUserMedia"),
        "short_title": _("getUserMedia"),
        "dateline": _("May 2013"),
        "short_dateline": _("May"),
        "tagline": _("Action!"),
        "summary": _("The getUserMedia function lets you access (with permission) the cameras and microphones of your users. No plugins needed! What can you do once you have this media? The possibilities are endless."),
        "description": _("The getUserMedia function lets you access (with permission) the cameras and microphones of your users. No plugins needed! What can you do once you have this media? The possibilities are endless."),
        "learn_more": [],
        "tab_copy": _("??"),
    },
    {
        "tag_name": "challenge:2013:june",
        "title": _("June 2013 Dev Derby Challenge - WebGL II"),
        "short_title": _("WebGL"),
        "dateline": _("June 2013"),
        "short_dateline": _("June"),
        "tagline": _("Twice the 3D!"),
        "summary": _("WebGL brings the power of OpenGL, for creating interactive 3D graphics, to the Web, with no plug-ins required."),
        "description": _("WebGL brings the power of OpenGL, for creating interactive 3D graphics, to the Web, with no plug-ins required."),
        "learn_more": [],
        "tab_copy": _("??"),
    },

    {
        "tag_name": "tech:audio",
        "title": _("Audio"),
        "description": _("Mozilla's Audio Data API extends the current HTML5 API and allows web developers to read and write raw audio data."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Introducing_the_Audio_API_Extension')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/HTML5_audio')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/html5/video.html#audio')),
        ),
    },
    {
        "tag_name": "tech:canvas",
        "title": _("Canvas"),
        "description": _("The HTML5 canvas element allows you to display scriptable renderings of 2D shapes and bitmap images."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/HTML/Canvas')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Canvas_element')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/html5/the-canvas-element.html')),
        ),
    },
    {
        "tag_name": "tech:css3",
        "title": _("CSS3"),
        "description": _("Cascading Style Sheets level 3 (CSS3) provide serveral new features and properties to enhance the formatting and look of documents written in different kinds of markup languages like HTML or XML."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/CSS')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Cascading_Style_Sheets')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/css3-roadmap/')),
        ),
    },
    {
        "tag_name": "tech:device",
        "title": _("Device"),
        "description": _("Media queries and orientation events let authors adjust their layout on hand-held devices such as mobile phones."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Detecting_device_orientation')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/css3-mediaqueries/')),
        ),
    },
    {
        "tag_name": "tech:files",
        "title": _("Files"),
        "description": _("The File API allows web developers to use file objects in web applications, as well as selecting and accessing their data."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/using_files_from_web_applications')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/FileAPI/')),
        ),
    },
    {
        "tag_name": "tech:fonts",
        "title": _("Fonts & Type"),
        "description": _("The CSS3-Font specification contains enhanced features for fonts and typography like  embedding own fonts via @font-face or controlling OpenType font features directly via CSS."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/css/@font-face')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Web_typography')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/css3-fonts/')),
        ),
    },
    {
        "tag_name": "tech:forms",
        "title": _("Forms"),
        "description": _("Form elements and attributes in HTML5 provide a greater degree of semantic mark-up than HTML4 and remove a great deal of the need for tedious scripting and styling that was required in HTML4."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/HTML/Forms_in_HTML')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/HTML_forms')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/html5/forms.html')),
        ),
    },
    {
        "tag_name": "tech:geolocation",
        "title": _("Geolocation"),
        "description": _("The Geolocation API allows web applications to access the user's geographical location."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Using_geolocation')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/W3C_Geolocation_API')),
            (_('W3C Spec'),          _('http://dev.w3.org/geo/api/spec-source.html')),
        ),
    },
    {
        "tag_name": "tech:javascript",
        "title": _("JavaScript"),
        "description": _("JavaScript is a lightweight, object-oriented programming language, commonly used for scripting interactive behavior on web pages and in web applications."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/javascript')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/JavaScript')),
            (_('ECMA Spec'),         _('http://www.ecma-international.org/publications/standards/Ecma-262.htm')),
        ),
    },
    {
        "tag_name": "tech:html5",
        "title": _("HTML5"),
        "description": _("HTML5 is the newest version of the HTML standard, currently under development."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/HTML/HTML5')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Html5')),
            (_('W3C Spec'),          _('http://dev.w3.org/html5/spec/Overview.html')),
        ),
    },
    {
        "tag_name": "tech:indexeddb",
        "title": _("IndexedDB"),
        "description": _("IndexedDB is an API for client-side storage of significant amounts of structured data and for high performance searches on this data using indexes. "),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/IndexedDB')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/IndexedDB')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/IndexedDB/')),
        ),
    },
    {
        "tag_name": "tech:dragndrop",
        "title": _("Drag and Drop"),
        "description": _("Drag and Drop features allow the user to move elements on the screen using the mouse pointer."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/DragDrop/Drag_and_Drop')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Drag-and-drop')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/html5/dnd.html')),
        ),
    },
    {
        "tag_name": "tech:mobile",
        "title": _("Mobile"),
        "description": _("Firefox Mobile brings the true Web experience to mobile phones and other non-PC devices."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Mobile')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Mobile_web')),
            (_('W3C Spec'),          _('http://www.w3.org/Mobile/')),
        ),
    },
    {
        "tag_name": "tech:offlinesupport",
        "title": _("Offline Support"),
        "description": _("Offline caching of web applications' resources using the application cache and local storage."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/dom/storage#localStorage')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Web_Storage')),
            (_('W3C Spec'),          _('http://dev.w3.org/html5/webstorage/')),
        ),
    },
    {
        "tag_name": "tech:svg",
        "title": _("SVG"),
        "description": _("Scalable Vector Graphics (SVG) is an XML based language for describing two-dimensional vector graphics."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/SVG')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Scalable_Vector_Graphics')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/SVG11/')),
        ),
    },
    {
        "tag_name": "tech:video",
        "title": _("Video"),
        "description": _("The HTML5 video element provides integrated support for playing video media without requiring plug-ins."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/Using_HTML5_audio_and_video')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/HTML5_video')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/html5/video.html')),
        ),
    },
    {
        "tag_name": "tech:webgl",
        "title": _("WebGL"),
        "description": _("In the context of the HTML canvas element WebGL provides an API for 3D graphics in the browser."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/WebGL')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/WebGL')),
            (_('Khronos Spec'),      _('http://www.khronos.org/webgl/')),
        ),
    },
    {
        "tag_name": "tech:websockets",
        "title": _("WebSockets"),
        "description": _("WebSockets is a technology that makes it possible to open an interactive  communication session between the user's browser and a server."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/WebSockets')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Web_Sockets')),
            (_('W3C Spec'),          _('http://dev.w3.org/html5/websockets/')),
        ),
    },
    {
        "tag_name": "tech:webworkers",
        "title": _("Web Workers"),
        "description": _("Web Workers provide a simple means for web content to run scripts in background threads."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/DOM/Using_web_workers')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Web_Workers')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/workers/')),
        ),
    },
    {
        "tag_name": "tech:xhr",
        "title": _("XMLHttpRequest"),
        "description": _("XMLHttpRequest (XHR) is used to send HTTP requests directly to a webserver and load the response data directly back into the script."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/DOM/XMLHttpRequest/Using_XMLHttpRequest')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/XMLHttpRequest')),
            (_('W3C Spec'),          _('http://www.w3.org/TR/XMLHttpRequest/')),
        ),
    },
    {
        "tag_name": "tech:multitouch",
        "title": _("Multi-touch"),
        "description": _("Track the movement of the user's finger on a touch screen, monitoring the raw touch events generated by the system."),
        "learn_more": (
            (_('MDN Documentation'), _('https://developer.mozilla.org/en-US/docs/DOM/Touch_events')),
            (_('Wikipedia Article'), _('http://en.wikipedia.org/wiki/Multi-touch')),
            (_('W3C Spec'),          _('http://www.w3.org/2010/webevents/charter/')),
        ),
    },
)))

# HACK: For easier L10N, define license in code instead of as a DB model
DEMO_LICENSES = dict((x['name'], x) for x in getattr(settings, 'DEMO_LICENSES', (
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
        x_offset + int(crop_width), y_offset + int(crop_height)))
    img = img.resize((dst_width, dst_height), Image.ANTIALIAS)

    if img.mode != "RGB":
        img = img.convert("RGB")
    new_img = StringIO()
    img.save(new_img, "JPEG")
    img_data = new_img.getvalue()

    return ContentFile(img_data)
