# -*- coding: utf-8 -*-
from redirect_urls import redirect as lib_redirect

from kuma.core.decorators import shared_cache_control


shared_cache_control_for_zones = shared_cache_control(
    s_maxage=60 * 60 * 24 * 7)


def get_sub_path_handler(root_path):
    def get_path(request, sub_path):
        return root_path + (sub_path or '')
    return get_path


def redirect(pattern, to, **kwargs):
    """
    Return a url matcher suited for urlpatterns

    Changes the defaults for locale_prefix and prepend_locale in the
    redirect_urls library.
    """
    return lib_redirect(pattern, to, locale_prefix=False,
                        prepend_locale=False, **kwargs)


def locale_redirect(pattern, to, prepend_locale=True, **kwargs):
    """
    Return a locale url matcher suited for urlpatterns

    This is suited for matching URLs that may start with a locale, like:

    /en-US/docs/Foo/Bar

    If the locale is a valid locale, the pattern matches against the remaining
    path:

    locale=/en-US, path=/docs/Foo/Bar

    However, many prefix strings match, so watch out for unintended matches:

    /docs/Foo/Bar

    can be matched as:

    locale=/docs, path=Foo/Bar
    """
    return lib_redirect(pattern, to, locale_prefix=True,
                        prepend_locale=prepend_locale, **kwargs)


# Redirects/rewrites/aliases migrated from SCL3 httpd config
scl3_redirectpatterns = [
    # RewriteRule ^/media/(redesign/)?css/(.*)-min.css$
    # /static/build/styles/$2.css [L,R=301]
    redirect(r'^media/(?:redesign/)?css/(?P<doc>.*)-min.css$',
             '/static/build/styles/{doc}.css',
             permanent=True),

    # RewriteRule ^/media/(redesign/)?js/(.*)-min.js$ /static/build/js/$2.js
    # [L,R=301]
    redirect(r'^media/(?:redesign/)?js/(?P<doc>.*)-min.js$',
             '/static/build/js/{doc}.js',
             permanent=True),

    # RewriteRule ^/media/(redesign/)?img(.*) /static/img$2 [L,R=301]
    redirect(r'^media/(?:redesign/)?img(?P<suffix>.*)$',
             '/static/img{suffix}',
             permanent=True),

    # RewriteRule ^/media/(redesign/)?css(.*) /static/styles$2 [L,R=301]
    redirect(r'^media/(?:redesign/)?css(?P<suffix>.*)$',
             '/static/styles{suffix}',
             permanent=True),

    # RewriteRule ^/media/(redesign/)?js(.*) /static/js$2 [L,R=301]
    redirect(r'^media/(?:redesign/)?js(?P<suffix>.*)$',
             '/static/js{suffix}',
             permanent=True),

    # RewriteRule ^/media/(redesign/)?fonts(.*) /static/fonts$2 [L,R=301]
    redirect(r'^media/(?:redesign/)?fonts(?P<suffix>.*)$',
             '/static/fonts{suffix}',
             permanent=True),

    # RedirectMatch 302 /media/uploads/demos/(.*)$
    # https://developer.mozilla.org/docs/Web/Demos_of_open_web_technologies/
    # Django will then redirect based on Accept-Language
    redirect(r'^media/uploads/demos/(?:.*)$',
             '/docs/Web/Demos_of_open_web_technologies/',
             permanent=False),

    # RewriteRule ^(.*)//(.*)//(.*)$ $1_$2_$3 [R=301,L,NC]
    redirect(r'^(?P<one>.*)//(?P<two>.*)//(?P<three>.*)$',
             '/{one}_{two}_{three}',
             re_flags='i', permanent=True),

    # RewriteRule ^(.*)//(.*)$ $1_$2 [R=301,L,NC]
    redirect(r'^(?P<one>.*)//(?P<two>.*)$',
             '/{one}_{two}',
             re_flags='i', permanent=True),

    # The remaining redirects don't show explicit RewriteRule as comments,
    # as they're all in the style of "static URL A now points at static URL B"

    # Bug 1078186 - Redirect old static canvas examples to wiki pages
    # canvas tutorial
    redirect(
        r'^samples/canvas-tutorial/2_1_canvas_rect.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Rectangular_shape_example',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/2_2_canvas_moveto.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Moving_the_pen',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/2_3_canvas_lineto.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Lines',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/2_4_canvas_arc.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Arcs',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/2_5_canvas_quadraticcurveto.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Quadratic_Bezier_curves',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/2_6_canvas_beziercurveto.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Cubic_Bezier_curves',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/3_1_canvas_drawimage.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Using_images#Drawing_images',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/3_2_canvas_drawimage.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Using_images#Example.3A_Tiling_an_image',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/3_3_canvas_drawimage.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Using_images#Example.3A_Framing_an_image',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/3_4_canvas_gallery.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Using_images#Art_gallery_example',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_1_canvas_fillstyle.html$',
        '/docs/Web/API/CanvasRenderingContext2D.fillStyle',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_2_canvas_strokestyle.html$',
        '/docs/Web/API/CanvasRenderingContext2D.strokeStyle',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_3_canvas_globalalpha.html$',
        '/docs/Web/API/CanvasRenderingContext2D.globalAlpha',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_4_canvas_rgba.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#An_example_using_rgba()',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_5_canvas_linewidth.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_lineWidth_example',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_6_canvas_linecap.html$',
        '/docs/Web/API/CanvasRenderingContext2D.lineCap',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_7_canvas_linejoin.html$',
        '/docs/Web/API/CanvasRenderingContext2D.lineJoin',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_8_canvas_miterlimit.html$',
        '/docs/Web/API/CanvasRenderingContext2D.miterLimit',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_9_canvas_lineargradient.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_createLinearGradient_example',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_10_canvas_radialgradient.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_createRadialGradient_example',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_11_canvas_createpattern.html$',
        '/docs/Web/API/CanvasRenderingContext2D.createPattern',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/5_1_canvas_savestate.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Transformations#A_save_and_restore_canvas_state_example',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/5_2_canvas_translate.html$',
        '/docs/Web/API/CanvasRenderingContext2D.translate',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/5_3_canvas_rotate.html$',
        '/docs/Web/API/CanvasRenderingContext2D.rotate',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/5_4_canvas_scale.html$',
        '/docs/Web/API/CanvasRenderingContext2D.scale',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/6_1_canvas_composite.html$',
        '/docs/Web/API/CanvasRenderingContext2D.globalCompositeOperation',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/6_2_canvas_clipping.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Compositing#Clipping_paths',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/globalCompositeOperation.html$',
        '/docs/Web/API/CanvasRenderingContext2D.globalCompositeOperation',
        re_flags='i', permanent=True),

    ##################################
    # MOZILLADEMOS
    ##################################
    # canvas images
    redirect(
        r'^samples/canvas-tutorial/images/backdrop.png$',
        'https://mdn.mozillademos.org/files/5395/backdrop.png',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/bg_gallery.png$',
        'https://mdn.mozillademos.org/files/5415/bg_gallery.png',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_1.jpg$',
        'https://mdn.mozillademos.org/files/5399/gallery_1.jpg',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_2.jpg$',
        'https://mdn.mozillademos.org/files/5401/gallery_2.jpg',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_3.jpg$',
        'https://mdn.mozillademos.org/files/5403/gallery_3.jpg',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_4.jpg$',
        'https://mdn.mozillademos.org/files/5405/gallery_4.jpg',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_5.jpg$',
        'https://mdn.mozillademos.org/files/5407/gallery_5.jpg',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_6.jpg$',
        'https://mdn.mozillademos.org/files/5409/gallery_6.jpg',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_7.jpg$',
        'https://mdn.mozillademos.org/files/5411/gallery_7.jpg',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_8.jpg$',
        'https://mdn.mozillademos.org/files/5413/gallery_8.jpg',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/picture_frame.png$',
        'https://mdn.mozillademos.org/files/242/Canvas_picture_frame.png',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/rhino.jpg$',
        'https://mdn.mozillademos.org/files/5397/rhino.jpg',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/wallpaper.png$',
        'https://mdn.mozillademos.org/files/222/Canvas_createpattern.png',
        re_flags='i', permanent=True),

    # canvas example in samples/domref
    redirect(
        r'^samples/domref/mozGetAsFile.html$',
        '/docs/Web/API/HTMLCanvasElement.mozGetAsFile',
        re_flags='i', permanent=True),


    ##################################
    # MDN.GITHUB.IO
    ##################################
    # canvas raycaster
    redirect(
        r'^samples/raycaster/input.js$',
        'http://mdn.github.io/canvas-raycaster/input.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/raycaster/Level.js$',
        'http://mdn.github.io/canvas-raycaster/Level.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/raycaster/Player.js$',
        'http://mdn.github.io/canvas-raycaster/Player.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/raycaster/RayCaster.html$',
        'http://mdn.github.io/canvas-raycaster/index.html',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/raycaster/RayCaster.js$',
        'http://mdn.github.io/canvas-raycaster/RayCaster.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/raycaster/trace.css$',
        'http://mdn.github.io/canvas-raycaster/trace.css',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/raycaster/trace.js$',
        'http://mdn.github.io/canvas-raycaster/trace.js',
        re_flags='i', permanent=True),


    # Bug 1215255 - Redirect static WebGL examples
    redirect(
        r'^samples/webgl/sample1$',
        'http://mdn.github.io/webgl-examples/tutorial/sample1',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample1/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample1/index.html',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample1/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample1/webgl-demo.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample1/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample2$',
        'http://mdn.github.io/webgl-examples/tutorial/sample2',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample2/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample2/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample2/index.html',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample2/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample2/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample2/webgl-demo.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample2/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample3$',
        'http://mdn.github.io/webgl-examples/tutorial/sample3',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample3/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample3/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample3/index.html',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample3/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample3/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample3/webgl-demo.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample3/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample4$',
        'http://mdn.github.io/webgl-examples/tutorial/sample4',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample4/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample4/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample4/index.html',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample4/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample4/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample4/webgl-demo.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample4/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample5$',
        'http://mdn.github.io/webgl-examples/tutorial/sample5',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample5/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample5/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample5/index.html',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample5/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample5/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample5/webgl-demo.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample5/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample6$',
        'http://mdn.github.io/webgl-examples/tutorial/sample6',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample6/cubetexture.png$',
        'http://mdn.github.io/webgl-examples/tutorial/sample6/cubetexture.png',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample6/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample6/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample6/index.html',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample6/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample6/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample6/webgl-demo.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample6/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample7$',
        'http://mdn.github.io/webgl-examples/tutorial/sample7',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample7/cubetexture.png$',
        'http://mdn.github.io/webgl-examples/tutorial/sample7/cubetexture.png',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample7/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample7/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample7/index.html',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample7/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample7/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample7/webgl-demo.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample7/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample8$',
        'http://mdn.github.io/webgl-examples/tutorial/sample8',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample8/Firefox.ogv$',
        'http://mdn.github.io/webgl-examples/tutorial/sample8/Firefox.ogv',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample8/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample8/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample8/index.html',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample8/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample8/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample8/webgl-demo.js',
        re_flags='i', permanent=True),

    redirect(
        r'^samples/webgl/sample8/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', permanent=True),

    # Bug 887428 - Misprinted URL in promo materials
    # RewriteRule ^Firefox_OS/Security$ docs/Mozilla/Firefox_OS/Security
    # [R=301,L,NC]
    redirect(
        r'^Firefox_OS/Security$',
        '/docs/Mozilla/Firefox_OS/Security',
        re_flags='i', permanent=True),

    # Old landing pages. The regex, adapted from Bedrock, captures locale prefixes.
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?mobile/?$ /$1docs/Mozilla/Mobile
    # [R=301,L]
    locale_redirect(
        r'^?mobile/?$',
        '/docs/Mozilla/Mobile',
        permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?addons/?$ /$1Add-ons [R=301,L]
    locale_redirect(
        r'^?addons/?$',
        '/Add-ons',
        permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?mozilla/?$ /$1docs/Mozilla [R=301,L]
    locale_redirect(
        r'^?mozilla/?$',
        '/docs/Mozilla',
        permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?web/?$ /$1docs/Web [R=301,L]
    locale_redirect(
        r'^?web/?$',
        '/docs/Web',
        permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?learn/html5/?$
    # /$1docs/Web/Guide/HTML/HTML5 [R=301,L]
    locale_redirect(
        r'^?learn/html5/?$',
        '/docs/Web/Guide/HTML/HTML5',
        permanent=True),

    # Some blanket section moves / renames
    # RewriteRule ^En/JavaScript/Reference/Objects/Array$
    # en-US/docs/JavaScript/Reference/Global_Objects/Array [R=301,L,NC]
    redirect(
        r'^En/JavaScript/Reference/Objects/Array$',
        '/en-US/docs/JavaScript/Reference/Global_Objects/Array',
        re_flags='i', permanent=True),

    # RewriteRule ^En/JavaScript/Reference/Objects$
    # en-US/docs/JavaScript/Reference/Global_Objects/Object [R=301,L,NC]
    redirect(
        r'^En/JavaScript/Reference/Objects$',
        '/en-US/docs/JavaScript/Reference/Global_Objects/Object',
        re_flags='i', permanent=True),

    # RewriteRule ^En/Core_JavaScript_1\.5_Reference/Objects/(.*)
    # en-US/docs/JavaScript/Reference/Global_Objects/$1 [R=301,L,NC]
    redirect(
        r'^En/Core_JavaScript_1\.5_Reference/Objects/(?P<suffix>.*)$',
        '/en-US/docs/JavaScript/Reference/Global_Objects/{suffix}',
        re_flags='i', permanent=True),

    # RewriteRule ^En/Core_JavaScript_1\.5_Reference/(.*)
    # en-US/docs/JavaScript/Reference/$1 [R=301,L,NC]
    redirect(
        r'^En/Core_JavaScript_1\.5_Reference/(?P<suffix>.*)$',
        '/en-US/docs/JavaScript/Reference/{suffix}',
        re_flags='i', permanent=True),

    # RewriteRule ^([\w\-]*)/HTML5$ $1/docs/HTML/HTML5 [R=301,L,NC]
    locale_redirect(
        r'^HTML5$',
        '/docs/HTML/HTML5',
        re_flags='i', permanent=True),

    # RewriteRule web-tech/2008/09/12/css-transforms
    # /docs/CSS/Using_CSS_transforms [R=301,L]
    redirect(
        r'^web-tech/2008/09/12/css-transforms$',
        '/docs/CSS/Using_CSS_transforms',
        permanent=True),

    # RewriteRule ^([\w\-]*)/docs/?$ $1/docs/Web [R=301,L,NC]
    locale_redirect(
        r'^/docs/?$',
        '/docs/Web',
        re_flags='i', permanent=True),

    # DevNews
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?devnews/index.php/feed.*
    # https://blog.mozilla.org/feed/ [R=301,L]
    locale_redirect(
        r'^?devnews/index.php/feed.*',
        'https://blog.mozilla.org/feed/',
        prepend_locale=False, permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?devnews.*
    # https://wiki.mozilla.org/Releases [R=301,L]
    locale_redirect(
        r'?devnews.*',
        'https://wiki.mozilla.org/Releases',
        prepend_locale=False, permanent=True),

    # Old "Learn" pages
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?learn/html /$1Learn/HTML [R=301,L]
    locale_redirect(
        r'?learn/html',
        # TODO: new path '/docs/Learn/HTML',
        '/Learn/HTML',
        permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?learn/css /$1Learn/CSS [R=301,L]
    locale_redirect(
        r'?learn/css',
        # TODO: new path '/docs/Learn/CSS',
        '/Learn/CSS',
        permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?learn/javascript /$1Learn/JavaScript
    # [R=301,L]
    locale_redirect(
        r'^?learn/javascript',
        # TODO: new path '/docs/Learn/JavaScript',
        '/Learn/JavaScript',
        permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?learn /$1Learn [R=301,L]
    locale_redirect(
        r'^?learn',
        # TODO: new path '/docs/Learn',
        '/Learn',
        permanent=True),

    # BananaBread demo (bug 1238041)
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?demos/detail/bananabread$
    # https://github.com/kripken/BananaBread/ [R=301,L]
    locale_redirect(
        r'^?demos/detail/bananabread$',
        'https://github.com/kripken/BananaBread/',
        prepend_locale=False, permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?demos/detail/bananabread/launch$
    # https://kripken.github.io/BananaBread/cube2/index.html [R=301,L]
    locale_redirect(
        r'^?demos/detail/bananabread/launch$',
        'https://kripken.github.io/BananaBread/cube2/index.html',
        prepend_locale=False, permanent=True),


    # All other Demo Studio and Dev Derby paths (bug 1238037)
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?demos
    # /$1docs/Web/Demos_of_open_web_technologies? [R=301,L]
    locale_redirect(
        r'^?demos',
        '/docs/Web/Demos_of_open_web_technologies',
        permanent=True),

    # Legacy off-site redirects (bug 1362438)
    # RewriteRule ^contests/ http://www.mozillalabs.com/ [R=302,L]
    redirect(r'^contests', 'http://www.mozillalabs.com/', permanent=False),

    # RewriteRule ^es4 http://www.ecma-international.org/memento/TC39.htm [R=302,L]
    redirect(r'^es4', 'http://www.ecma-international.org/memento/TC39.htm',
             permanent=False),
]

zone_redirectpatterns = [
    # The redirects for the case when the locale is not specified
    # for a zone. It must be handled here, since for the cases when
    # LocaleMiddleware handles the 404 response and redirects to the
    # proper locale, it fails because the path is considered invalid.
    redirect(
        r'^(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^(?:docs/)?Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/docs/Web/Apps'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^Learn(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/docs/Learn'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^(?:docs/)?Marketplace(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/docs/Mozilla/Marketplace'),
        permanent=False,
        decorators=shared_cache_control_for_zones),

    # The locale-specific redirects for the "Add-ons" zone.
    redirect(
        r'^af/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/af/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ar/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ar/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^bn-BD/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/bn-BD/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^bn-IN/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/bn-IN/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ca/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ca/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^cs/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/cs/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^de/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/de/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^el/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/el/docs/Mozilla/Πρόσθετα'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^en-US/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/en-US/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^es/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/es/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^fa/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/fa/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^fr/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/fr/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^hu/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/hu/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^id/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/id/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^it/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/it/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ja/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ja/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ko/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ko/docs/Mozilla/애드온들'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ms/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ms/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^nl/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/nl/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^pl/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/pl/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^pt-BR/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/pt-BR/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^pt-PT/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/pt-PT/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ro/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ro/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ru/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ru/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^sv-SE/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/sv-SE/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^th/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/th/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^uk/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/uk/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^vi/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/vi/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^zh-CN/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/zh-CN/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^zh-TW/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/zh-TW/docs/Mozilla/Add-ons'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^tr/(?:docs/)?Add-ons(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/tr/docs/Mozilla/Eklentiler'),
        permanent=False,
        decorators=shared_cache_control_for_zones),

    # The locale-specific redirects for the "Firefox" zone.
    redirect(
        r'^af/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/af/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ar/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ar/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^az/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/az/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^bm/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/bm/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^bn-BD/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/bn-BD/docs/Mozilla/ফায়ারফক্স'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^bn-IN/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/bn-IN/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ca/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ca/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^cs/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/cs/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^de/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/de/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ee/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ee/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^el/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/el/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^en-US/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/en-US/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^es/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/es/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ff/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ff/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^fi/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/fi/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^fr/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/fr/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^fy-NL/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/fy-NL/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ga-IE/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ga-IE/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ha/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ha/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^he/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/he/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^hi-IN/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/hi-IN/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^hr/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/hr/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^hu/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/hu/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^id/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/id/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ig/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ig/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^it/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/it/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ja/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ja/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ka/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ka/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ko/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ko/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ln/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ln/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ml/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ml/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ms/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ms/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^my/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/my/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^nl/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/nl/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^pl/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/pl/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^pt-BR/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/pt-BR/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^pt-PT/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/pt-PT/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ro/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ro/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ru/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ru/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^son/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/son/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^sq/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/sq/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^sv-SE/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/sv-SE/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^sw/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/sw/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ta/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ta/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^th/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/th/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^tl/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/tl/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^tr/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/tr/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^vi/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/vi/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^wo/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/wo/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^xh/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/xh/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^yo/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/yo/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^zh-CN/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/zh-CN/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^zh-TW/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/zh-TW/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^zu/(?:docs/)?Firefox(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/zu/docs/Mozilla/Firefox'),
        permanent=False,
        decorators=shared_cache_control_for_zones),

    # The locale-specific redirects for the "Apps" zone.
    redirect(
        r'^bn-BD/Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/bn-BD/docs/Apps'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^de/Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/de/docs/Apps'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^en-US/(?:docs/)?Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/en-US/docs/Web/Apps'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^es/(?:docs/)?Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/es/docs/Web/Aplicaciones'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^fa/(?:docs/)?Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/fa/docs/Web/Apps'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^fr/(?:docs/)?Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/fr/docs/Web/Apps'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^it/Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/it/docs/Apps'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ja/(?:docs/)?Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ja/docs/Web/Apps'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ko/Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ko/docs/Apps'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^pt-BR/Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/pt-BR/docs/Apps'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ru/Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ru/docs/Apps'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ta/(?:docs/)?Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ta/docs/Web/Apps'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^th/(?:docs/)?Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/th/docs/Web/Apps'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^zh-CN/(?:docs/)?Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/zh-CN/docs/Web/Apps'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^zh-TW/(?:docs/)?Apps(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/zh-TW/docs/Web/Apps'),
        permanent=False,
        decorators=shared_cache_control_for_zones),

    # The locale-specific redirects for the "Learn" zone.
    redirect(
        r'^ca/Learn(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ca/docs/Learn'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^de/Learn(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/de/docs/Learn'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^fr/Apprendre(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/fr/docs/Apprendre'),
        permanent=False,
        decorators=shared_cache_control_for_zones),

    # The locale-specific redirects for the "Marketplace" zone.
    redirect(
        r'^de/(?:docs/)?Marketplace(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/de/docs/Mozilla/Marketplace'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^en-US/(?:docs/)?Marketplace(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/en-US/docs/Mozilla/Marketplace'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^es/(?:docs/)?Marketplace(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/es/docs/Mozilla/Marketplace'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^fa/(?:docs/)?Marketplace(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/fa/docs/Mozilla/بازار'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^fr/(?:docs/)?Marketplace(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/fr/docs/Mozilla/Marketplace'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^it/(?:docs/)?Marketplace(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/it/docs/Mozilla/Marketplace'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^ja/(?:docs/)?Marketplace(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/ja/docs/Mozilla/Marketplace'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
    redirect(
        r'^zh-CN/(?:docs/)?Marketplace(?:/?|(?P<sub_path>[/$].+))$',
        get_sub_path_handler(u'/zh-CN/docs/Mozilla/Marketplace'),
        permanent=False,
        decorators=shared_cache_control_for_zones),
]

redirectpatterns = scl3_redirectpatterns + zone_redirectpatterns + [
    locale_redirect(
        r'^fellowship',
        '/docs/Archive/2015_MDN_Fellowship_Program',
        permanent=True),
]
