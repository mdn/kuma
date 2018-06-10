# -*- coding: utf-8 -*-
import requests

from utils.urls import flatten, url_test


# Converted from SCL3 Apache files
SCL3_REDIRECT_URLS = list(flatten((
    url_test("/media/redesign/css/foo-min.css",
             "/static/build/styles/foo.css"),
    url_test("/media/css/foo-min.css", "/static/build/styles/foo.css"),

    url_test("/media/redesign/js/foo-min.js", "/static/build/js/foo.js"),
    url_test("/media/js/foo-min.js", "/static/build/js/foo.js"),

    url_test("/media/redesign/img.foo", "/static/img.foo"),
    url_test("/media/img.foo", "/static/img.foo"),

    url_test("/media/redesign/css.foo", "/static/styles.foo"),
    url_test("/media/css.foo", "/static/styles.foo"),

    url_test("/media/redesign/js.foo", "/static/js.foo"),
    url_test("/media/js.foo", "/static/js.foo"),

    url_test("/media/redesign/fonts.foo", "/static/fonts.foo"),
    url_test("/media/fonts.foo", "/static/fonts.foo"),

    url_test("/media/uploads/demos/foobar123",
             "/docs/Web/Demos_of_open_web_technologies/",
             status_code=requests.codes.found),

    url_test("/docs/Mozilla/Projects/NSPR/Reference/I//O_Functions",
             "/docs/Mozilla/Projects/NSPR/Reference/I_O_Functions"),
    url_test("/docs/Mozilla/Projects/NSPR/Reference/I//O//Functions",
             "/docs/Mozilla/Projects/NSPR/Reference/I_O_Functions"),

    url_test("/samples/canvas-tutorial/2_1_canvas_rect.html",
             "/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Rectangular_shape_example"),
    url_test("/samples/canvas-tutorial/2_2_canvas_moveto.html",
             "/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Moving_the_pen"),
    url_test("/samples/canvas-tutorial/2_3_canvas_lineto.html",
             "/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Lines"),
    url_test("/samples/canvas-tutorial/2_4_canvas_arc.html",
             "/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Arcs"),
    url_test("/samples/canvas-tutorial/2_5_canvas_quadraticcurveto.html",
             "/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Quadratic_Bezier_curves"),
    url_test("/samples/canvas-tutorial/2_6_canvas_beziercurveto.html",
             "/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Cubic_Bezier_curves"),
    url_test("/samples/canvas-tutorial/3_1_canvas_drawimage.html",
             "/docs/Web/API/Canvas_API/Tutorial/Using_images#Drawing_images"),
    url_test("/samples/canvas-tutorial/3_2_canvas_drawimage.html",
             "/docs/Web/API/Canvas_API/Tutorial/Using_images#Example.3A_Tiling_an_image"),
    url_test("/samples/canvas-tutorial/3_3_canvas_drawimage.html",
             "/docs/Web/API/Canvas_API/Tutorial/Using_images#Example.3A_Framing_an_image"),
    url_test("/samples/canvas-tutorial/3_4_canvas_gallery.html",
             "/docs/Web/API/Canvas_API/Tutorial/Using_images#Art_gallery_example"),
    url_test("/samples/canvas-tutorial/4_1_canvas_fillstyle.html",
             "/docs/Web/API/CanvasRenderingContext2D.fillStyle"),
    url_test("/samples/canvas-tutorial/4_2_canvas_strokestyle.html",
             "/docs/Web/API/CanvasRenderingContext2D.strokeStyle"),
    url_test("/samples/canvas-tutorial/4_3_canvas_globalalpha.html",
             "/docs/Web/API/CanvasRenderingContext2D.globalAlpha"),
    url_test("/samples/canvas-tutorial/4_4_canvas_rgba.html",
             "/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#An_example_using_rgba()"),
    url_test("/samples/canvas-tutorial/4_5_canvas_linewidth.html",
             "/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_lineWidth_example"),
    url_test("/samples/canvas-tutorial/4_6_canvas_linecap.html",
             "/docs/Web/API/CanvasRenderingContext2D.lineCap"),
    url_test("/samples/canvas-tutorial/4_7_canvas_linejoin.html",
             "/docs/Web/API/CanvasRenderingContext2D.lineJoin"),
    url_test("/samples/canvas-tutorial/4_8_canvas_miterlimit.html",
             "/docs/Web/API/CanvasRenderingContext2D.miterLimit"),
    url_test("/samples/canvas-tutorial/4_9_canvas_lineargradient.html",
             "/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_createLinearGradient_example"),
    url_test("/samples/canvas-tutorial/4_10_canvas_radialgradient.html",
             "/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_createRadialGradient_example"),
    url_test("/samples/canvas-tutorial/4_11_canvas_createpattern.html",
             "/docs/Web/API/CanvasRenderingContext2D.createPattern"),
    url_test("/samples/canvas-tutorial/5_1_canvas_savestate.html",
             "/docs/Web/API/Canvas_API/Tutorial/Transformations#A_save_and_restore_canvas_state_example"),
    url_test("/samples/canvas-tutorial/5_2_canvas_translate.html",
             "/docs/Web/API/CanvasRenderingContext2D.translate"),
    url_test("/samples/canvas-tutorial/5_3_canvas_rotate.html",
             "/docs/Web/API/CanvasRenderingContext2D.rotate"),
    url_test("/samples/canvas-tutorial/5_4_canvas_scale.html",
             "/docs/Web/API/CanvasRenderingContext2D.scale"),
    url_test("/samples/canvas-tutorial/6_1_canvas_composite.html",
             "/docs/Web/API/CanvasRenderingContext2D.globalCompositeOperation"),
    url_test("/samples/canvas-tutorial/6_2_canvas_clipping.html",
             "/docs/Web/API/Canvas_API/Tutorial/Compositing#Clipping_paths"),
    url_test("/samples/canvas-tutorial/globalCompositeOperation.html",
             "/docs/Web/API/CanvasRenderingContext2D.globalCompositeOperation"),

    url_test("/samples/domref/mozGetAsFile.html",
             "/docs/Web/API/HTMLCanvasElement.mozGetAsFile"),

    url_test("/Firefox_OS/Security", "/docs/Mozilla/Firefox_OS/Security"),

    url_test("/en-US/mobile", "/en-US/docs/Mozilla/Mobile"),
    url_test("/en-US/mobile/", "/en-US/docs/Mozilla/Mobile"),
    url_test("/en/mobile/", "/en/docs/Mozilla/Mobile"),

    url_test("/en-US/addons", "/en-US/Add-ons"),
    url_test("/en-US/addons/", "/en-US/Add-ons"),
    url_test("/en/addons/", "/en/Add-ons"),

    url_test("/en-US/mozilla", "/en-US/docs/Mozilla"),
    url_test("/en-US/mozilla/", "/en-US/docs/Mozilla"),
    url_test("/en/mozilla/", "/en/docs/Mozilla"),

    url_test("/en-US/web", "/en-US/docs/Web"),
    url_test("/en-US/web/", "/en-US/docs/Web"),
    url_test("/en/web/", "/en/docs/Web"),

    url_test("/en-US/learn/html5", "/en-US/docs/Web/Guide/HTML/HTML5"),
    url_test("/en-US/learn/html5/", "/en-US/docs/Web/Guide/HTML/HTML5"),
    url_test("/en/learn/html5/", "/en/docs/Web/Guide/HTML/HTML5"),

    url_test("/En/JavaScript/Reference/Objects/Array",
             "/en-US/docs/JavaScript/Reference/Global_Objects/Array"),
    url_test("/En/JavaScript/Reference/Objects",
             "/en-US/docs/JavaScript/Reference/Global_Objects/Object"),
    url_test("/En/Core_JavaScript_1.5_Reference/Objects/foo",
             "/en-US/docs/JavaScript/Reference/Global_Objects/foo"),
    url_test("/En/Core_JavaScript_1.5_Reference/foo",
             "/en-US/docs/JavaScript/Reference/foo"),

    url_test("/en-US/HTML5", "/en-US/docs/HTML/HTML5"),
    url_test("/es/HTML5", "/es/docs/HTML/HTML5"),

    url_test("/web-tech/2008/09/12/css-transforms",
             "/docs/CSS/Using_CSS_transforms"),

    url_test("/en-US/docs", "/en-US/docs/Web"),
    url_test("/es/docs/", "/es/docs/Web"),

    url_test("/en-US/devnews/index.php/feed.foo",
             "https://blog.mozilla.org/feed/"),
    url_test("/en-US/devnews/foo", "https://wiki.mozilla.org/Releases"),

    url_test("/en-US/learn/html", "/en-US/Learn/HTML"),
    url_test("/en/learn/html", "/en/Learn/HTML"),

    url_test("/en-US/learn/css", "/en-US/Learn/CSS"),
    url_test("/en/learn/css", "/en/Learn/CSS"),

    url_test("/en-US/learn/javascript", "/en-US/Learn/JavaScript"),
    url_test("/en/learn/javascript", "/en/Learn/JavaScript"),

    url_test("/en-US/learn", "/en-US/Learn"),
    url_test("/en/learn", "/en/Learn"),

    url_test("/en-US/demos/detail/bananabread",
             "https://github.com/kripken/BananaBread/"),
    url_test("/en/demos/detail/bananabread",
             "https://github.com/kripken/BananaBread/"),

    url_test("/en-US/demos/detail/bananabread/launch",
             "https://kripken.github.io/BananaBread/cube2/index.html"),
    url_test("/en/demos/detail/bananabread/launch",
             "https://kripken.github.io/BananaBread/cube2/index.html"),

    url_test("/en-US/demos", "/en-US/docs/Web/Demos_of_open_web_technologies"),
    url_test("/en/demos", "/en/docs/Web/Demos_of_open_web_technologies"),
)))

# Converted from SCL3 Apache files - demos moved to GitHub
GITHUB_IO_URLS = list(flatten((
    # http://mdn.github.io
    # canvas raycaster
    url_test("/samples/raycaster/input.js",
             "http://mdn.github.io/canvas-raycaster/input.js"),
    url_test("/samples/raycaster/Level.js",
             "http://mdn.github.io/canvas-raycaster/Level.js"),
    url_test("/samples/raycaster/Player.js",
             "http://mdn.github.io/canvas-raycaster/Player.js"),
    url_test("/samples/raycaster/RayCaster.html",
             "http://mdn.github.io/canvas-raycaster/index.html"),
    url_test("/samples/raycaster/RayCaster.js",
             "http://mdn.github.io/canvas-raycaster/RayCaster.js"),
    url_test("/samples/raycaster/trace.css",
             "http://mdn.github.io/canvas-raycaster/trace.css"),
    url_test("/samples/raycaster/trace.js",
             "http://mdn.github.io/canvas-raycaster/trace.js"),

    # Bug 1215255 - Redirect static WebGL examples
    url_test("/samples/webgl/sample1",
             "http://mdn.github.io/webgl-examples/tutorial/sample1"),
    url_test("/samples/webgl/sample1/index.html",
             "http://mdn.github.io/webgl-examples/tutorial/sample1/index.html"),
    url_test("/samples/webgl/sample1/webgl-demo.js",
             "http://mdn.github.io/webgl-examples/tutorial/sample1/webgl-demo.js"),
    url_test("/samples/webgl/sample1/webgl.css",
             "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
    url_test("/samples/webgl/sample2",
             "http://mdn.github.io/webgl-examples/tutorial/sample2"),
    url_test("/samples/webgl/sample2/glUtils.js",
             "http://mdn.github.io/webgl-examples/tutorial/glUtils.js"),
    url_test("/samples/webgl/sample2/index.html",
             "http://mdn.github.io/webgl-examples/tutorial/sample2/index.html"),
    url_test("/samples/webgl/sample2/sylvester.js",
             "http://mdn.github.io/webgl-examples/tutorial/sylvester.js"),
    url_test("/samples/webgl/sample2/webgl-demo.js",
             "http://mdn.github.io/webgl-examples/tutorial/sample2/webgl-demo.js"),
    url_test("/samples/webgl/sample2/webgl.css",
             "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
    url_test("/samples/webgl/sample3",
             "http://mdn.github.io/webgl-examples/tutorial/sample3"),
    url_test("/samples/webgl/sample3/glUtils.js",
             "http://mdn.github.io/webgl-examples/tutorial/glUtils.js"),
    url_test("/samples/webgl/sample3/index.html",
             "http://mdn.github.io/webgl-examples/tutorial/sample3/index.html"),
    url_test("/samples/webgl/sample3/sylvester.js",
             "http://mdn.github.io/webgl-examples/tutorial/sylvester.js"),
    url_test("/samples/webgl/sample3/webgl-demo.js",
             "http://mdn.github.io/webgl-examples/tutorial/sample3/webgl-demo.js"),
    url_test("/samples/webgl/sample3/webgl.css",
             "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
    url_test("/samples/webgl/sample4",
             "http://mdn.github.io/webgl-examples/tutorial/sample4"),
    url_test("/samples/webgl/sample4/glUtils.js",
             "http://mdn.github.io/webgl-examples/tutorial/glUtils.js"),
    url_test("/samples/webgl/sample4/index.html",
             "http://mdn.github.io/webgl-examples/tutorial/sample4/index.html"),
    url_test("/samples/webgl/sample4/sylvester.js",
             "http://mdn.github.io/webgl-examples/tutorial/sylvester.js"),
    url_test("/samples/webgl/sample4/webgl-demo.js",
             "http://mdn.github.io/webgl-examples/tutorial/sample4/webgl-demo.js"),
    url_test("/samples/webgl/sample4/webgl.css",
             "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
    url_test("/samples/webgl/sample5",
             "http://mdn.github.io/webgl-examples/tutorial/sample5"),
    url_test("/samples/webgl/sample5/glUtils.js",
             "http://mdn.github.io/webgl-examples/tutorial/glUtils.js"),
    url_test("/samples/webgl/sample5/index.html",
             "http://mdn.github.io/webgl-examples/tutorial/sample5/index.html"),
    url_test("/samples/webgl/sample5/sylvester.js",
             "http://mdn.github.io/webgl-examples/tutorial/sylvester.js"),
    url_test("/samples/webgl/sample5/webgl-demo.js",
             "http://mdn.github.io/webgl-examples/tutorial/sample5/webgl-demo.js"),
    url_test("/samples/webgl/sample5/webgl.css",
             "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
    url_test("/samples/webgl/sample6",
             "http://mdn.github.io/webgl-examples/tutorial/sample6"),
    url_test("/samples/webgl/sample6/cubetexture.png",
             "http://mdn.github.io/webgl-examples/tutorial/sample6/cubetexture.png"),
    url_test("/samples/webgl/sample6/glUtils.js",
             "http://mdn.github.io/webgl-examples/tutorial/glUtils.js"),
    url_test("/samples/webgl/sample6/index.html",
             "http://mdn.github.io/webgl-examples/tutorial/sample6/index.html"),
    url_test("/samples/webgl/sample6/sylvester.js",
             "http://mdn.github.io/webgl-examples/tutorial/sylvester.js"),
    url_test("/samples/webgl/sample6/webgl-demo.js",
             "http://mdn.github.io/webgl-examples/tutorial/sample6/webgl-demo.js"),
    url_test("/samples/webgl/sample6/webgl.css",
             "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
    url_test("/samples/webgl/sample7",
             "http://mdn.github.io/webgl-examples/tutorial/sample7"),
    url_test("/samples/webgl/sample7/cubetexture.png",
             "http://mdn.github.io/webgl-examples/tutorial/sample7/cubetexture.png"),
    url_test("/samples/webgl/sample7/glUtils.js",
             "http://mdn.github.io/webgl-examples/tutorial/glUtils.js"),
    url_test("/samples/webgl/sample7/index.html",
             "http://mdn.github.io/webgl-examples/tutorial/sample7/index.html"),
    url_test("/samples/webgl/sample7/sylvester.js",
             "http://mdn.github.io/webgl-examples/tutorial/sylvester.js"),
    url_test("/samples/webgl/sample7/webgl-demo.js",
             "http://mdn.github.io/webgl-examples/tutorial/sample7/webgl-demo.js"),
    url_test("/samples/webgl/sample7/webgl.css",
             "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
    url_test("/samples/webgl/sample8",
             "http://mdn.github.io/webgl-examples/tutorial/sample8"),
    url_test("/samples/webgl/sample8/Firefox.ogv",
             "http://mdn.github.io/webgl-examples/tutorial/sample8/Firefox.ogv"),
    url_test("/samples/webgl/sample8/glUtils.js",
             "http://mdn.github.io/webgl-examples/tutorial/glUtils.js"),
    url_test("/samples/webgl/sample8/index.html",
             "http://mdn.github.io/webgl-examples/tutorial/sample8/index.html"),
    url_test("/samples/webgl/sample8/sylvester.js",
             "http://mdn.github.io/webgl-examples/tutorial/sylvester.js"),
    url_test("/samples/webgl/sample8/webgl-demo.js",
             "http://mdn.github.io/webgl-examples/tutorial/sample8/webgl-demo.js"),
    url_test("/samples/webgl/sample8/webgl.css",
             "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
)))

# Converted from SCL3 Apache files - move to untrusted domain
MOZILLADEMOS_URLS = list(flatten((
    # https://mdn.mozillademos.org/
    url_test("/samples/canvas-tutorial/images/backdrop.png",
             "https://mdn.mozillademos.org/files/5395/backdrop.png"),
    url_test("/samples/canvas-tutorial/images/bg_gallery.png",
             "https://mdn.mozillademos.org/files/5415/bg_gallery.png"),
    url_test("/samples/canvas-tutorial/images/gallery_1.jpg",
             "https://mdn.mozillademos.org/files/5399/gallery_1.jpg"),
    url_test("/samples/canvas-tutorial/images/gallery_2.jpg",
             "https://mdn.mozillademos.org/files/5401/gallery_2.jpg"),
    url_test("/samples/canvas-tutorial/images/gallery_3.jpg",
             "https://mdn.mozillademos.org/files/5403/gallery_3.jpg"),
    url_test("/samples/canvas-tutorial/images/gallery_4.jpg",
             "https://mdn.mozillademos.org/files/5405/gallery_4.jpg"),
    url_test("/samples/canvas-tutorial/images/gallery_5.jpg",
             "https://mdn.mozillademos.org/files/5407/gallery_5.jpg"),
    url_test("/samples/canvas-tutorial/images/gallery_6.jpg",
             "https://mdn.mozillademos.org/files/5409/gallery_6.jpg"),
    url_test("/samples/canvas-tutorial/images/gallery_7.jpg",
             "https://mdn.mozillademos.org/files/5411/gallery_7.jpg"),
    url_test("/samples/canvas-tutorial/images/gallery_8.jpg",
             "https://mdn.mozillademos.org/files/5413/gallery_8.jpg"),
    url_test("/samples/canvas-tutorial/images/picture_frame.png",
             "https://mdn.mozillademos.org/files/242/Canvas_picture_frame.png"),
    url_test("/samples/canvas-tutorial/images/rhino.jpg",
             "https://mdn.mozillademos.org/files/5397/rhino.jpg"),
    url_test("/samples/canvas-tutorial/images/wallpaper.png",
             "https://mdn.mozillademos.org/files/222/Canvas_createpattern.png"),
)))

# Converted from SCL3 Apache files - MindTouch / old hosted files
LEGACY_URLS = list(flatten((
    # bug 1362438
    url_test('/index.php', status_code=404),
    url_test('/index.php?title=Special:Recentchanges&feed=atom',
             status_code=404),
    url_test('/index.php?title=En/HTML/Canvas&revision=11',
             status_code=404),
    url_test('/index.php?title=En/HTML/Canvas&revision=11',
             status_code=404),
    url_test('/patches', status_code=404),
    url_test('/patches/foo', status_code=404),
    url_test('/web-tech', status_code=404),
    url_test('/web-tech/feed/atom/', status_code=404),
    url_test('/css/wiki.css', status_code=404),
    url_test('/css/base.css', status_code=404),
    url_test('/contests', 'http://www.mozillalabs.com/', status_code=302),
    url_test('/contests/', 'http://www.mozillalabs.com/', status_code=302),
    url_test('/contests/extendfirefox/faq.php', 'http://www.mozillalabs.com/',
             status_code=302),
    url_test('/es4', 'http://www.ecma-international.org/memento/TC39.htm',
             status_code=302),
    url_test('/es4/', 'http://www.ecma-international.org/memento/TC39.htm',
             status_code=302),
    url_test('/es4/proposals/slice_syntax.html',
             'http://www.ecma-international.org/memento/TC39.htm',
             status_code=302),
    # bug 962148
    url_test('/en/docs/Web/CSS/Attribute_selectors',
             '/en-US/docs/Web/CSS/Attribute_selectors', status_code=302),
    url_test('/en/docs/Web/CSS/Attribute_selectors',
             '/en-US/docs/Web/CSS/Attribute_selectors', status_code=302),
    url_test('/cn/docs/Talk:Kakurady', '/zh-CN/docs/Talk:Kakurady',
             status_code=302),
    url_test('/zh_cn/docs/Web/API/RTCPeerConnection/addTrack',
             '/zh-CN/docs/Web/API/RTCPeerConnection/addTrack',
             status_code=302),
    url_test('/zh_tw/docs/AJAX', '/zh-TW/docs/AJAX', status_code=302),
)))

ZONE_REDIRECT_URLS = list(flatten((
    url_test(u'/Add-ons',
             u'/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Add-ons/',
             u'/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Add-ons/WebExtensions',
             u'/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Add-ons$edit',
             u'/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/docs/Add-ons',
             u'/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),

    url_test(u'/af/Add-ons',
             u'/af/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/af/Add-ons/',
             u'/af/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/af/Add-ons/WebExtensions',
             u'/af/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/af/Add-ons$edit',
             u'/af/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/af/docs/Add-ons',
             u'/af/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ar/Add-ons',
             u'/ar/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ar/Add-ons/',
             u'/ar/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ar/Add-ons/WebExtensions',
             u'/ar/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ar/Add-ons$edit',
             u'/ar/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ar/docs/Add-ons',
             u'/ar/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-BD/Add-ons',
             u'/bn-BD/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-BD/Add-ons/',
             u'/bn-BD/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-BD/Add-ons/WebExtensions',
             u'/bn-BD/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-BD/Add-ons$edit',
             u'/bn-BD/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-BD/docs/Add-ons',
             u'/bn-BD/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-IN/Add-ons',
             u'/bn-IN/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-IN/Add-ons/',
             u'/bn-IN/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-IN/Add-ons/WebExtensions',
             u'/bn-IN/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-IN/Add-ons$edit',
             u'/bn-IN/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-IN/docs/Add-ons',
             u'/bn-IN/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ca/Add-ons',
             u'/ca/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ca/Add-ons/',
             u'/ca/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ca/Add-ons/WebExtensions',
             u'/ca/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ca/Add-ons$edit',
             u'/ca/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ca/docs/Add-ons',
             u'/ca/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/cs/Add-ons',
             u'/cs/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/cs/Add-ons/',
             u'/cs/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/cs/Add-ons/WebExtensions',
             u'/cs/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/cs/Add-ons$edit',
             u'/cs/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/cs/docs/Add-ons',
             u'/cs/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Add-ons',
             u'/de/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Add-ons/',
             u'/de/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Add-ons/WebExtensions',
             u'/de/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Add-ons$edit',
             u'/de/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/docs/Add-ons',
             u'/de/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/el/Add-ons',
             u'/el/docs/Mozilla/Πρόσθετα',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/el/Add-ons/',
             u'/el/docs/Mozilla/Πρόσθετα',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/el/Add-ons/WebExtensions',
             u'/el/docs/Mozilla/Πρόσθετα/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/el/Add-ons$edit',
             u'/el/docs/Mozilla/Πρόσθετα$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/el/docs/Add-ons',
             u'/el/docs/Mozilla/Πρόσθετα',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Add-ons',
             u'/en-US/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Add-ons/',
             u'/en-US/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Add-ons/WebExtensions',
             u'/en-US/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Add-ons$edit',
             u'/en-US/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/docs/Add-ons',
             u'/en-US/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Add-ons',
             u'/es/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Add-ons/',
             u'/es/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Add-ons/WebExtensions',
             u'/es/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Add-ons$edit',
             u'/es/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/docs/Add-ons',
             u'/es/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fa/Add-ons',
             u'/fa/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fa/Add-ons/',
             u'/fa/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fa/Add-ons/WebExtensions',
             u'/fa/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fa/Add-ons$edit',
             u'/fa/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fa/docs/Add-ons',
             u'/fa/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Add-ons',
             u'/fr/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Add-ons/',
             u'/fr/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Add-ons/WebExtensions',
             u'/fr/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Add-ons$edit',
             u'/fr/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/docs/Add-ons',
             u'/fr/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hu/Add-ons',
             u'/hu/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hu/Add-ons/',
             u'/hu/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hu/Add-ons/WebExtensions',
             u'/hu/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hu/Add-ons$edit',
             u'/hu/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hu/docs/Add-ons',
             u'/hu/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/id/Add-ons',
             u'/id/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/id/Add-ons/',
             u'/id/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/id/Add-ons/WebExtensions',
             u'/id/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/id/Add-ons$edit',
             u'/id/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/id/docs/Add-ons',
             u'/id/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Add-ons',
             u'/it/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Add-ons/',
             u'/it/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Add-ons/WebExtensions',
             u'/it/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Add-ons$edit',
             u'/it/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/docs/Add-ons',
             u'/it/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Add-ons',
             u'/ja/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Add-ons/',
             u'/ja/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Add-ons/WebExtensions',
             u'/ja/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Add-ons$edit',
             u'/ja/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/docs/Add-ons',
             u'/ja/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ko/Add-ons',
             u'/ko/docs/Mozilla/애드온들',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ko/Add-ons/',
             u'/ko/docs/Mozilla/애드온들',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ko/Add-ons/WebExtensions',
             u'/ko/docs/Mozilla/애드온들/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ko/Add-ons$edit',
             u'/ko/docs/Mozilla/애드온들$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ko/docs/Add-ons',
             u'/ko/docs/Mozilla/애드온들',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ms/Add-ons',
             u'/ms/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ms/Add-ons/',
             u'/ms/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ms/Add-ons/WebExtensions',
             u'/ms/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ms/Add-ons$edit',
             u'/ms/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ms/docs/Add-ons',
             u'/ms/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/nl/Add-ons',
             u'/nl/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/nl/Add-ons/',
             u'/nl/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/nl/Add-ons/WebExtensions',
             u'/nl/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/nl/Add-ons$edit',
             u'/nl/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/nl/docs/Add-ons',
             u'/nl/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pl/Add-ons',
             u'/pl/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pl/Add-ons/',
             u'/pl/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pl/Add-ons/WebExtensions',
             u'/pl/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pl/Add-ons$edit',
             u'/pl/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pl/docs/Add-ons',
             u'/pl/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-BR/Add-ons',
             u'/pt-BR/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-BR/Add-ons/',
             u'/pt-BR/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-BR/Add-ons/WebExtensions',
             u'/pt-BR/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-BR/Add-ons$edit',
             u'/pt-BR/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-BR/docs/Add-ons',
             u'/pt-BR/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-PT/Add-ons',
             u'/pt-PT/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-PT/Add-ons/',
             u'/pt-PT/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-PT/Add-ons/WebExtensions',
             u'/pt-PT/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-PT/Add-ons$edit',
             u'/pt-PT/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-PT/docs/Add-ons',
             u'/pt-PT/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ro/Add-ons',
             u'/ro/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ro/Add-ons/',
             u'/ro/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ro/Add-ons/WebExtensions',
             u'/ro/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ro/Add-ons$edit',
             u'/ro/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ro/docs/Add-ons',
             u'/ro/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ru/Add-ons',
             u'/ru/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ru/Add-ons/',
             u'/ru/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ru/Add-ons/WebExtensions',
             u'/ru/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ru/Add-ons$edit',
             u'/ru/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ru/docs/Add-ons',
             u'/ru/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sv-SE/Add-ons',
             u'/sv-SE/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sv-SE/Add-ons/',
             u'/sv-SE/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sv-SE/Add-ons/WebExtensions',
             u'/sv-SE/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sv-SE/Add-ons$edit',
             u'/sv-SE/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sv-SE/docs/Add-ons',
             u'/sv-SE/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/th/Add-ons',
             u'/th/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/th/Add-ons/',
             u'/th/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/th/Add-ons/WebExtensions',
             u'/th/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/th/Add-ons$edit',
             u'/th/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/th/docs/Add-ons',
             u'/th/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/uk/Add-ons',
             u'/uk/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/uk/Add-ons/',
             u'/uk/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/uk/Add-ons/WebExtensions',
             u'/uk/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/uk/Add-ons$edit',
             u'/uk/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/uk/docs/Add-ons',
             u'/uk/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/vi/Add-ons',
             u'/vi/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/vi/Add-ons/',
             u'/vi/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/vi/Add-ons/WebExtensions',
             u'/vi/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/vi/Add-ons$edit',
             u'/vi/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/vi/docs/Add-ons',
             u'/vi/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Add-ons',
             u'/zh-CN/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Add-ons/',
             u'/zh-CN/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Add-ons/WebExtensions',
             u'/zh-CN/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Add-ons$edit',
             u'/zh-CN/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/docs/Add-ons',
             u'/zh-CN/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-TW/Add-ons',
             u'/zh-TW/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-TW/Add-ons/',
             u'/zh-TW/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-TW/Add-ons/WebExtensions',
             u'/zh-TW/docs/Mozilla/Add-ons/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-TW/Add-ons$edit',
             u'/zh-TW/docs/Mozilla/Add-ons$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-TW/docs/Add-ons',
             u'/zh-TW/docs/Mozilla/Add-ons',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/tr/Add-ons',
             u'/tr/docs/Mozilla/Eklentiler',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/tr/Add-ons/',
             u'/tr/docs/Mozilla/Eklentiler',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/tr/Add-ons/WebExtensions',
             u'/tr/docs/Mozilla/Eklentiler/WebExtensions',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/tr/Add-ons$edit',
             u'/tr/docs/Mozilla/Eklentiler$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/tr/docs/Add-ons',
             u'/tr/docs/Mozilla/Eklentiler',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Firefox',
             u'/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Firefox/',
             u'/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Firefox/Privacy',
             u'/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Firefox$edit',
             u'/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/docs/Firefox',
             u'/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/af/Firefox',
             u'/af/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/af/Firefox/',
             u'/af/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/af/Firefox/Privacy',
             u'/af/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/af/Firefox$edit',
             u'/af/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/af/docs/Firefox',
             u'/af/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ar/Firefox',
             u'/ar/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ar/Firefox/',
             u'/ar/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ar/Firefox/Privacy',
             u'/ar/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ar/Firefox$edit',
             u'/ar/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ar/docs/Firefox',
             u'/ar/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/az/Firefox',
             u'/az/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/az/Firefox/',
             u'/az/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/az/Firefox/Privacy',
             u'/az/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/az/Firefox$edit',
             u'/az/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/az/docs/Firefox',
             u'/az/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bm/Firefox',
             u'/bm/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bm/Firefox/',
             u'/bm/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bm/Firefox/Privacy',
             u'/bm/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bm/Firefox$edit',
             u'/bm/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bm/docs/Firefox',
             u'/bm/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-BD/Firefox',
             u'/bn-BD/docs/Mozilla/ফায়ারফক্স',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-BD/Firefox/',
             u'/bn-BD/docs/Mozilla/ফায়ারফক্স',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-BD/Firefox/Privacy',
             u'/bn-BD/docs/Mozilla/ফায়ারফক্স/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-BD/Firefox$edit',
             u'/bn-BD/docs/Mozilla/ফায়ারফক্স$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-BD/docs/Firefox',
             u'/bn-BD/docs/Mozilla/ফায়ারফক্স',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-IN/Firefox',
             u'/bn-IN/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-IN/Firefox/',
             u'/bn-IN/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-IN/Firefox/Privacy',
             u'/bn-IN/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-IN/Firefox$edit',
             u'/bn-IN/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-IN/docs/Firefox',
             u'/bn-IN/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ca/Firefox',
             u'/ca/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ca/Firefox/',
             u'/ca/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ca/Firefox/Privacy',
             u'/ca/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ca/Firefox$edit',
             u'/ca/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ca/docs/Firefox',
             u'/ca/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/cs/Firefox',
             u'/cs/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/cs/Firefox/',
             u'/cs/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/cs/Firefox/Privacy',
             u'/cs/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/cs/Firefox$edit',
             u'/cs/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/cs/docs/Firefox',
             u'/cs/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Firefox',
             u'/de/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Firefox/',
             u'/de/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Firefox/Privacy',
             u'/de/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Firefox$edit',
             u'/de/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/docs/Firefox',
             u'/de/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ee/Firefox',
             u'/ee/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ee/Firefox/',
             u'/ee/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ee/Firefox/Privacy',
             u'/ee/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ee/Firefox$edit',
             u'/ee/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ee/docs/Firefox',
             u'/ee/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/el/Firefox',
             u'/el/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/el/Firefox/',
             u'/el/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/el/Firefox/Privacy',
             u'/el/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/el/Firefox$edit',
             u'/el/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/el/docs/Firefox',
             u'/el/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Firefox',
             u'/en-US/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Firefox/',
             u'/en-US/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Firefox/Privacy',
             u'/en-US/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Firefox$edit',
             u'/en-US/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/docs/Firefox',
             u'/en-US/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Firefox',
             u'/es/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Firefox/',
             u'/es/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Firefox/Privacy',
             u'/es/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Firefox$edit',
             u'/es/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/docs/Firefox',
             u'/es/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ff/Firefox',
             u'/ff/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ff/Firefox/',
             u'/ff/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ff/Firefox/Privacy',
             u'/ff/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ff/Firefox$edit',
             u'/ff/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ff/docs/Firefox',
             u'/ff/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fi/Firefox',
             u'/fi/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fi/Firefox/',
             u'/fi/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fi/Firefox/Privacy',
             u'/fi/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fi/Firefox$edit',
             u'/fi/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fi/docs/Firefox',
             u'/fi/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Firefox',
             u'/fr/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Firefox/',
             u'/fr/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Firefox/Privacy',
             u'/fr/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Firefox$edit',
             u'/fr/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/docs/Firefox',
             u'/fr/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fy-NL/Firefox',
             u'/fy-NL/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fy-NL/Firefox/',
             u'/fy-NL/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fy-NL/Firefox/Privacy',
             u'/fy-NL/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fy-NL/Firefox$edit',
             u'/fy-NL/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fy-NL/docs/Firefox',
             u'/fy-NL/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ga-IE/Firefox',
             u'/ga-IE/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ga-IE/Firefox/',
             u'/ga-IE/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ga-IE/Firefox/Privacy',
             u'/ga-IE/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ga-IE/Firefox$edit',
             u'/ga-IE/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ga-IE/docs/Firefox',
             u'/ga-IE/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ha/Firefox',
             u'/ha/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ha/Firefox/',
             u'/ha/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ha/Firefox/Privacy',
             u'/ha/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ha/Firefox$edit',
             u'/ha/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ha/docs/Firefox',
             u'/ha/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/he/Firefox',
             u'/he/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/he/Firefox/',
             u'/he/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/he/Firefox/Privacy',
             u'/he/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/he/Firefox$edit',
             u'/he/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/he/docs/Firefox',
             u'/he/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hi-IN/Firefox',
             u'/hi-IN/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hi-IN/Firefox/',
             u'/hi-IN/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hi-IN/Firefox/Privacy',
             u'/hi-IN/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hi-IN/Firefox$edit',
             u'/hi-IN/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hi-IN/docs/Firefox',
             u'/hi-IN/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hr/Firefox',
             u'/hr/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hr/Firefox/',
             u'/hr/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hr/Firefox/Privacy',
             u'/hr/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hr/Firefox$edit',
             u'/hr/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hr/docs/Firefox',
             u'/hr/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hu/Firefox',
             u'/hu/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hu/Firefox/',
             u'/hu/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hu/Firefox/Privacy',
             u'/hu/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hu/Firefox$edit',
             u'/hu/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/hu/docs/Firefox',
             u'/hu/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/id/Firefox',
             u'/id/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/id/Firefox/',
             u'/id/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/id/Firefox/Privacy',
             u'/id/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/id/Firefox$edit',
             u'/id/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/id/docs/Firefox',
             u'/id/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ig/Firefox',
             u'/ig/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ig/Firefox/',
             u'/ig/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ig/Firefox/Privacy',
             u'/ig/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ig/Firefox$edit',
             u'/ig/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ig/docs/Firefox',
             u'/ig/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Firefox',
             u'/it/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Firefox/',
             u'/it/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Firefox/Privacy',
             u'/it/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Firefox$edit',
             u'/it/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/docs/Firefox',
             u'/it/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Firefox',
             u'/ja/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Firefox/',
             u'/ja/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Firefox/Privacy',
             u'/ja/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Firefox$edit',
             u'/ja/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/docs/Firefox',
             u'/ja/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ka/Firefox',
             u'/ka/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ka/Firefox/',
             u'/ka/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ka/Firefox/Privacy',
             u'/ka/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ka/Firefox$edit',
             u'/ka/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ka/docs/Firefox',
             u'/ka/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ko/Firefox',
             u'/ko/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ko/Firefox/',
             u'/ko/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ko/Firefox/Privacy',
             u'/ko/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ko/Firefox$edit',
             u'/ko/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ko/docs/Firefox',
             u'/ko/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ln/Firefox',
             u'/ln/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ln/Firefox/',
             u'/ln/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ln/Firefox/Privacy',
             u'/ln/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ln/Firefox$edit',
             u'/ln/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ln/docs/Firefox',
             u'/ln/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ml/Firefox',
             u'/ml/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ml/Firefox/',
             u'/ml/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ml/Firefox/Privacy',
             u'/ml/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ml/Firefox$edit',
             u'/ml/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ml/docs/Firefox',
             u'/ml/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ms/Firefox',
             u'/ms/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ms/Firefox/',
             u'/ms/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ms/Firefox/Privacy',
             u'/ms/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ms/Firefox$edit',
             u'/ms/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ms/docs/Firefox',
             u'/ms/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/my/Firefox',
             u'/my/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/my/Firefox/',
             u'/my/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/my/Firefox/Privacy',
             u'/my/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/my/Firefox$edit',
             u'/my/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/my/docs/Firefox',
             u'/my/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/nl/Firefox',
             u'/nl/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/nl/Firefox/',
             u'/nl/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/nl/Firefox/Privacy',
             u'/nl/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/nl/Firefox$edit',
             u'/nl/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/nl/docs/Firefox',
             u'/nl/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pl/Firefox',
             u'/pl/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pl/Firefox/',
             u'/pl/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pl/Firefox/Privacy',
             u'/pl/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pl/Firefox$edit',
             u'/pl/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pl/docs/Firefox',
             u'/pl/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-BR/Firefox',
             u'/pt-BR/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-BR/Firefox/',
             u'/pt-BR/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-BR/Firefox/Privacy',
             u'/pt-BR/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-BR/Firefox$edit',
             u'/pt-BR/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-BR/docs/Firefox',
             u'/pt-BR/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-PT/Firefox',
             u'/pt-PT/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-PT/Firefox/',
             u'/pt-PT/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-PT/Firefox/Privacy',
             u'/pt-PT/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-PT/Firefox$edit',
             u'/pt-PT/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-PT/docs/Firefox',
             u'/pt-PT/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ro/Firefox',
             u'/ro/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ro/Firefox/',
             u'/ro/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ro/Firefox/Privacy',
             u'/ro/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ro/Firefox$edit',
             u'/ro/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ro/docs/Firefox',
             u'/ro/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ru/Firefox',
             u'/ru/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ru/Firefox/',
             u'/ru/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ru/Firefox/Privacy',
             u'/ru/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ru/Firefox$edit',
             u'/ru/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ru/docs/Firefox',
             u'/ru/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/son/Firefox',
             u'/son/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/son/Firefox/',
             u'/son/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/son/Firefox/Privacy',
             u'/son/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/son/Firefox$edit',
             u'/son/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/son/docs/Firefox',
             u'/son/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sq/Firefox',
             u'/sq/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sq/Firefox/',
             u'/sq/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sq/Firefox/Privacy',
             u'/sq/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sq/Firefox$edit',
             u'/sq/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sq/docs/Firefox',
             u'/sq/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sv-SE/Firefox',
             u'/sv-SE/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sv-SE/Firefox/',
             u'/sv-SE/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sv-SE/Firefox/Privacy',
             u'/sv-SE/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sv-SE/Firefox$edit',
             u'/sv-SE/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sv-SE/docs/Firefox',
             u'/sv-SE/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sw/Firefox',
             u'/sw/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sw/Firefox/',
             u'/sw/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sw/Firefox/Privacy',
             u'/sw/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sw/Firefox$edit',
             u'/sw/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/sw/docs/Firefox',
             u'/sw/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ta/Firefox',
             u'/ta/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ta/Firefox/',
             u'/ta/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ta/Firefox/Privacy',
             u'/ta/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ta/Firefox$edit',
             u'/ta/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ta/docs/Firefox',
             u'/ta/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/th/Firefox',
             u'/th/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/th/Firefox/',
             u'/th/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/th/Firefox/Privacy',
             u'/th/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/th/Firefox$edit',
             u'/th/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/th/docs/Firefox',
             u'/th/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/tl/Firefox',
             u'/tl/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/tl/Firefox/',
             u'/tl/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/tl/Firefox/Privacy',
             u'/tl/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/tl/Firefox$edit',
             u'/tl/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/tl/docs/Firefox',
             u'/tl/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/tr/Firefox',
             u'/tr/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/tr/Firefox/',
             u'/tr/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/tr/Firefox/Privacy',
             u'/tr/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/tr/Firefox$edit',
             u'/tr/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/tr/docs/Firefox',
             u'/tr/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/vi/Firefox',
             u'/vi/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/vi/Firefox/',
             u'/vi/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/vi/Firefox/Privacy',
             u'/vi/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/vi/Firefox$edit',
             u'/vi/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/vi/docs/Firefox',
             u'/vi/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/wo/Firefox',
             u'/wo/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/wo/Firefox/',
             u'/wo/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/wo/Firefox/Privacy',
             u'/wo/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/wo/Firefox$edit',
             u'/wo/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/wo/docs/Firefox',
             u'/wo/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/xh/Firefox',
             u'/xh/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/xh/Firefox/',
             u'/xh/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/xh/Firefox/Privacy',
             u'/xh/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/xh/Firefox$edit',
             u'/xh/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/xh/docs/Firefox',
             u'/xh/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/yo/Firefox',
             u'/yo/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/yo/Firefox/',
             u'/yo/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/yo/Firefox/Privacy',
             u'/yo/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/yo/Firefox$edit',
             u'/yo/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/yo/docs/Firefox',
             u'/yo/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Firefox',
             u'/zh-CN/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Firefox/',
             u'/zh-CN/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Firefox/Privacy',
             u'/zh-CN/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Firefox$edit',
             u'/zh-CN/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/docs/Firefox',
             u'/zh-CN/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-TW/Firefox',
             u'/zh-TW/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-TW/Firefox/',
             u'/zh-TW/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-TW/Firefox/Privacy',
             u'/zh-TW/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-TW/Firefox$edit',
             u'/zh-TW/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-TW/docs/Firefox',
             u'/zh-TW/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zu/Firefox',
             u'/zu/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zu/Firefox/',
             u'/zu/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zu/Firefox/Privacy',
             u'/zu/docs/Mozilla/Firefox/Privacy',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zu/Firefox$edit',
             u'/zu/docs/Mozilla/Firefox$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zu/docs/Firefox',
             u'/zu/docs/Mozilla/Firefox',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Apps',
             u'/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Apps/',
             u'/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Apps/Tutorials',
             u'/docs/Web/Apps/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Apps$edit',
             u'/docs/Web/Apps$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/docs/Apps',
             u'/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-BD/Apps',
             u'/bn-BD/docs/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-BD/Apps/',
             u'/bn-BD/docs/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-BD/Apps/Tutorials',
             u'/bn-BD/docs/Apps/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/bn-BD/Apps$edit',
             u'/bn-BD/docs/Apps$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Apps',
             u'/de/docs/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Apps/',
             u'/de/docs/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Apps/Tutorials',
             u'/de/docs/Apps/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Apps$edit',
             u'/de/docs/Apps$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Apps',
             u'/en-US/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Apps/',
             u'/en-US/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Apps/Tutorials',
             u'/en-US/docs/Web/Apps/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Apps$edit',
             u'/en-US/docs/Web/Apps$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/docs/Apps',
             u'/en-US/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Apps',
             u'/es/docs/Web/Aplicaciones',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Apps/',
             u'/es/docs/Web/Aplicaciones',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Apps/Tutorials',
             u'/es/docs/Web/Aplicaciones/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Apps$edit',
             u'/es/docs/Web/Aplicaciones$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/docs/Apps',
             u'/es/docs/Web/Aplicaciones',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fa/Apps',
             u'/fa/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fa/Apps/',
             u'/fa/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fa/Apps/Tutorials',
             u'/fa/docs/Web/Apps/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fa/Apps$edit',
             u'/fa/docs/Web/Apps$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fa/docs/Apps',
             u'/fa/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Apps',
             u'/fr/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Apps/',
             u'/fr/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Apps/Tutorials',
             u'/fr/docs/Web/Apps/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Apps$edit',
             u'/fr/docs/Web/Apps$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/docs/Apps',
             u'/fr/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Apps',
             u'/it/docs/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Apps/',
             u'/it/docs/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Apps/Tutorials',
             u'/it/docs/Apps/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Apps$edit',
             u'/it/docs/Apps$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Apps',
             u'/ja/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Apps/',
             u'/ja/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Apps/Tutorials',
             u'/ja/docs/Web/Apps/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Apps$edit',
             u'/ja/docs/Web/Apps$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/docs/Apps',
             u'/ja/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ko/Apps',
             u'/ko/docs/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ko/Apps/',
             u'/ko/docs/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ko/Apps/Tutorials',
             u'/ko/docs/Apps/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ko/Apps$edit',
             u'/ko/docs/Apps$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-BR/Apps',
             u'/pt-BR/docs/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-BR/Apps/',
             u'/pt-BR/docs/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-BR/Apps/Tutorials',
             u'/pt-BR/docs/Apps/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/pt-BR/Apps$edit',
             u'/pt-BR/docs/Apps$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ru/Apps',
             u'/ru/docs/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ru/Apps/',
             u'/ru/docs/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ru/Apps/Tutorials',
             u'/ru/docs/Apps/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ru/Apps$edit',
             u'/ru/docs/Apps$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ta/Apps',
             u'/ta/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ta/Apps/',
             u'/ta/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ta/Apps/Tutorials',
             u'/ta/docs/Web/Apps/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ta/Apps$edit',
             u'/ta/docs/Web/Apps$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ta/docs/Apps',
             u'/ta/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/th/Apps',
             u'/th/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/th/Apps/',
             u'/th/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/th/Apps/Tutorials',
             u'/th/docs/Web/Apps/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/th/Apps$edit',
             u'/th/docs/Web/Apps$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/th/docs/Apps',
             u'/th/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Apps',
             u'/zh-CN/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Apps/',
             u'/zh-CN/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Apps/Tutorials',
             u'/zh-CN/docs/Web/Apps/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Apps$edit',
             u'/zh-CN/docs/Web/Apps$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/docs/Apps',
             u'/zh-CN/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-TW/Apps',
             u'/zh-TW/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-TW/Apps/',
             u'/zh-TW/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-TW/Apps/Tutorials',
             u'/zh-TW/docs/Web/Apps/Tutorials',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-TW/Apps$edit',
             u'/zh-TW/docs/Web/Apps$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-TW/docs/Apps',
             u'/zh-TW/docs/Web/Apps',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Learn',
             u'/docs/Learn',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Learn/',
             u'/docs/Learn',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Learn/JavaScript',
             u'/docs/Learn/JavaScript',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Learn$edit',
             u'/docs/Learn$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ca/Learn',
             u'/ca/docs/Learn',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ca/Learn/',
             u'/ca/docs/Learn',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ca/Learn/JavaScript',
             u'/ca/docs/Learn/JavaScript',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ca/Learn$edit',
             u'/ca/docs/Learn$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Learn',
             u'/de/docs/Learn',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Learn/',
             u'/de/docs/Learn',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Learn/JavaScript',
             u'/de/docs/Learn/JavaScript',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Learn$edit',
             u'/de/docs/Learn$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Apprendre',
             u'/fr/docs/Apprendre',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Apprendre/',
             u'/fr/docs/Apprendre',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Apprendre/JavaScript',
             u'/fr/docs/Apprendre/JavaScript',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Apprendre$edit',
             u'/fr/docs/Apprendre$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Marketplace',
             u'/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Marketplace/',
             u'/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Marketplace/APIs',
             u'/docs/Mozilla/Marketplace/APIs',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/Marketplace$edit',
             u'/docs/Mozilla/Marketplace$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/docs/Marketplace',
             u'/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Marketplace',
             u'/de/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Marketplace/',
             u'/de/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Marketplace/APIs',
             u'/de/docs/Mozilla/Marketplace/APIs',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/Marketplace$edit',
             u'/de/docs/Mozilla/Marketplace$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/de/docs/Marketplace',
             u'/de/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Marketplace',
             u'/en-US/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Marketplace/',
             u'/en-US/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Marketplace/APIs',
             u'/en-US/docs/Mozilla/Marketplace/APIs',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/Marketplace$edit',
             u'/en-US/docs/Mozilla/Marketplace$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/en-US/docs/Marketplace',
             u'/en-US/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Marketplace',
             u'/es/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Marketplace/',
             u'/es/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Marketplace/APIs',
             u'/es/docs/Mozilla/Marketplace/APIs',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/Marketplace$edit',
             u'/es/docs/Mozilla/Marketplace$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/es/docs/Marketplace',
             u'/es/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fa/Marketplace',
             u'/fa/docs/Mozilla/بازار',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fa/Marketplace/',
             u'/fa/docs/Mozilla/بازار',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fa/Marketplace/APIs',
             u'/fa/docs/Mozilla/بازار/APIs',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fa/Marketplace$edit',
             u'/fa/docs/Mozilla/بازار$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fa/docs/Marketplace',
             u'/fa/docs/Mozilla/بازار',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Marketplace',
             u'/fr/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Marketplace/',
             u'/fr/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Marketplace/APIs',
             u'/fr/docs/Mozilla/Marketplace/APIs',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/Marketplace$edit',
             u'/fr/docs/Mozilla/Marketplace$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/fr/docs/Marketplace',
             u'/fr/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Marketplace',
             u'/it/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Marketplace/',
             u'/it/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Marketplace/APIs',
             u'/it/docs/Mozilla/Marketplace/APIs',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/Marketplace$edit',
             u'/it/docs/Mozilla/Marketplace$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/it/docs/Marketplace',
             u'/it/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Marketplace',
             u'/ja/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Marketplace/',
             u'/ja/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Marketplace/APIs',
             u'/ja/docs/Mozilla/Marketplace/APIs',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/Marketplace$edit',
             u'/ja/docs/Mozilla/Marketplace$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/ja/docs/Marketplace',
             u'/ja/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Marketplace',
             u'/zh-CN/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Marketplace/',
             u'/zh-CN/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Marketplace/APIs',
             u'/zh-CN/docs/Mozilla/Marketplace/APIs',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/Marketplace$edit',
             u'/zh-CN/docs/Mozilla/Marketplace$edit',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
    url_test(u'/zh-CN/docs/Marketplace',
             u'/zh-CN/docs/Mozilla/Marketplace',
             status_code=302,
             resp_headers={
                 'cache-control': 'max-age=0, public, s-maxage=604800'
             }),
)))

# Redirects added after 2017 AWS move
REDIRECT_URLS = list(flatten((
    url_test('/en-US/fellowship',
             '/en-US/docs/Archive/2015_MDN_Fellowship_Program'),
)))
