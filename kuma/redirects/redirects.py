from functools import partial

from django.conf import settings
from redirect_urls import redirect as lib_redirect

from kuma.core.decorators import shared_cache_control


shared_cache_control_for_zones = shared_cache_control(s_maxage=60 * 60 * 24 * 7)


def redirect(pattern, to, **kwargs):
    """
    Return a url matcher suited for urlpatterns

    Changes the defaults for locale_prefix and prepend_locale in the
    redirect_urls library.
    """
    return lib_redirect(
        pattern, to, locale_prefix=False, prepend_locale=False, **kwargs
    )


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
    return lib_redirect(
        pattern, to, locale_prefix=True, prepend_locale=prepend_locale, **kwargs
    )


# Redirects/rewrites/aliases migrated from SCL3 httpd config
scl3_redirectpatterns = [
    # RewriteRule ^/media/(redesign/)?css/(.*)-min.css$
    # /static/build/styles/$2.css [L,R=301]
    redirect(
        r"^media/(?:redesign/)?css/(?P<doc>.*)-min.css$",
        "/static/build/styles/{doc}.css",
        permanent=True,
    ),
    # RewriteRule ^/media/(redesign/)?js/(.*)-min.js$ /static/build/js/$2.js
    # [L,R=301]
    redirect(
        r"^media/(?:redesign/)?js/(?P<doc>.*)-min.js$",
        "/static/build/js/{doc}.js",
        permanent=True,
    ),
    # RewriteRule ^/media/(redesign/)?img(.*) /static/img$2 [L,R=301]
    redirect(
        r"^media/(?:redesign/)?img(?P<suffix>.*)$",
        "/static/img{suffix}",
        permanent=True,
    ),
    # RewriteRule ^/media/(redesign/)?css(.*) /static/styles$2 [L,R=301]
    redirect(
        r"^media/(?:redesign/)?css(?P<suffix>.*)$",
        "/static/styles{suffix}",
        permanent=True,
    ),
    # RewriteRule ^/media/(redesign/)?js(.*) /static/js$2 [L,R=301]
    redirect(
        r"^media/(?:redesign/)?js(?P<suffix>.*)$", "/static/js{suffix}", permanent=True
    ),
    # RewriteRule ^/media/(redesign/)?fonts(.*) /static/fonts$2 [L,R=301]
    redirect(
        r"^media/(?:redesign/)?fonts(?P<suffix>.*)$",
        "/static/fonts{suffix}",
        permanent=True,
    ),
    # RedirectMatch 302 /media/uploads/demos/(.*)$
    # https://developer.mozilla.org/docs/Web/Demos_of_open_web_technologies/
    # Django will then redirect based on Accept-Language
    redirect(
        r"^media/uploads/demos/(?:.*)$",
        "/docs/Web/Demos_of_open_web_technologies/",
        permanent=False,
    ),
    # RewriteRule ^(.*)//(.*)//(.*)$ $1_$2_$3 [R=301,L,NC]
    redirect(
        r"^(?P<one>.*)//(?P<two>.*)//(?P<three>.*)$",
        "/{one}_{two}_{three}",
        re_flags="i",
        permanent=True,
    ),
    # RewriteRule ^(.*)//(.*)$ $1_$2 [R=301,L,NC]
    redirect(
        r"^(?P<one>.*)//(?P<two>.*)$", "/{one}_{two}", re_flags="i", permanent=True
    ),
    # The remaining redirects don't show explicit RewriteRule as comments,
    # as they're all in the style of "static URL A now points at static URL B"
    # Bug 1078186 - Redirect old static canvas examples to wiki pages
    # canvas tutorial
    redirect(
        r"^samples/canvas-tutorial/2_1_canvas_rect.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Rectangular_shape_example",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/2_2_canvas_moveto.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Moving_the_pen",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/2_3_canvas_lineto.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Lines",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/2_4_canvas_arc.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Arcs",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/2_5_canvas_quadraticcurveto.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Quadratic_Bezier_curves",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/2_6_canvas_beziercurveto.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Cubic_Bezier_curves",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/3_1_canvas_drawimage.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Using_images#Drawing_images",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/3_2_canvas_drawimage.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Using_images#Example.3A_Tiling_an_image",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/3_3_canvas_drawimage.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Using_images#Example.3A_Framing_an_image",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/3_4_canvas_gallery.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Using_images#Art_gallery_example",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/4_1_canvas_fillstyle.html$",
        "/docs/Web/API/CanvasRenderingContext2D.fillStyle",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/4_2_canvas_strokestyle.html$",
        "/docs/Web/API/CanvasRenderingContext2D.strokeStyle",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/4_3_canvas_globalalpha.html$",
        "/docs/Web/API/CanvasRenderingContext2D.globalAlpha",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/4_4_canvas_rgba.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#An_example_using_rgba()",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/4_5_canvas_linewidth.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_lineWidth_example",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/4_6_canvas_linecap.html$",
        "/docs/Web/API/CanvasRenderingContext2D.lineCap",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/4_7_canvas_linejoin.html$",
        "/docs/Web/API/CanvasRenderingContext2D.lineJoin",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/4_8_canvas_miterlimit.html$",
        "/docs/Web/API/CanvasRenderingContext2D.miterLimit",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/4_9_canvas_lineargradient.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_createLinearGradient_example",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/4_10_canvas_radialgradient.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_createRadialGradient_example",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/4_11_canvas_createpattern.html$",
        "/docs/Web/API/CanvasRenderingContext2D.createPattern",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/5_1_canvas_savestate.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Transformations#A_save_and_restore_canvas_state_example",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/5_2_canvas_translate.html$",
        "/docs/Web/API/CanvasRenderingContext2D.translate",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/5_3_canvas_rotate.html$",
        "/docs/Web/API/CanvasRenderingContext2D.rotate",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/5_4_canvas_scale.html$",
        "/docs/Web/API/CanvasRenderingContext2D.scale",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/6_1_canvas_composite.html$",
        "/docs/Web/API/CanvasRenderingContext2D.globalCompositeOperation",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/6_2_canvas_clipping.html$",
        "/docs/Web/API/Canvas_API/Tutorial/Compositing#Clipping_paths",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/globalCompositeOperation.html$",
        "/docs/Web/API/CanvasRenderingContext2D.globalCompositeOperation",
        re_flags="i",
        permanent=True,
    ),
    ##################################
    # MOZILLADEMOS
    ##################################
    # canvas images
    redirect(
        r"^samples/canvas-tutorial/images/backdrop.png$",
        "https://mdn.mozillademos.org/files/5395/backdrop.png",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/images/bg_gallery.png$",
        "https://mdn.mozillademos.org/files/5415/bg_gallery.png",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/images/gallery_1.jpg$",
        "https://mdn.mozillademos.org/files/5399/gallery_1.jpg",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/images/gallery_2.jpg$",
        "https://mdn.mozillademos.org/files/5401/gallery_2.jpg",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/images/gallery_3.jpg$",
        "https://mdn.mozillademos.org/files/5403/gallery_3.jpg",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/images/gallery_4.jpg$",
        "https://mdn.mozillademos.org/files/5405/gallery_4.jpg",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/images/gallery_5.jpg$",
        "https://mdn.mozillademos.org/files/5407/gallery_5.jpg",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/images/gallery_6.jpg$",
        "https://mdn.mozillademos.org/files/5409/gallery_6.jpg",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/images/gallery_7.jpg$",
        "https://mdn.mozillademos.org/files/5411/gallery_7.jpg",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/images/gallery_8.jpg$",
        "https://mdn.mozillademos.org/files/5413/gallery_8.jpg",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/images/picture_frame.png$",
        "https://mdn.mozillademos.org/files/242/Canvas_picture_frame.png",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/images/rhino.jpg$",
        "https://mdn.mozillademos.org/files/5397/rhino.jpg",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/canvas-tutorial/images/wallpaper.png$",
        "https://mdn.mozillademos.org/files/222/Canvas_createpattern.png",
        re_flags="i",
        permanent=True,
    ),
    # canvas example in samples/domref
    redirect(
        r"^samples/domref/mozGetAsFile.html$",
        "/docs/Web/API/HTMLCanvasElement.mozGetAsFile",
        re_flags="i",
        permanent=True,
    ),
    ##################################
    # MDN.GITHUB.IO
    ##################################
    # canvas raycaster
    redirect(
        r"^samples/raycaster/input.js$",
        "http://mdn.github.io/canvas-raycaster/input.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/raycaster/Level.js$",
        "http://mdn.github.io/canvas-raycaster/Level.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/raycaster/Player.js$",
        "http://mdn.github.io/canvas-raycaster/Player.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/raycaster/RayCaster.html$",
        "http://mdn.github.io/canvas-raycaster/index.html",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/raycaster/RayCaster.js$",
        "http://mdn.github.io/canvas-raycaster/RayCaster.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/raycaster/trace.css$",
        "http://mdn.github.io/canvas-raycaster/trace.css",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/raycaster/trace.js$",
        "http://mdn.github.io/canvas-raycaster/trace.js",
        re_flags="i",
        permanent=True,
    ),
    # Bug 1215255 - Redirect static WebGL examples
    redirect(
        r"^samples/webgl/sample1$",
        "http://mdn.github.io/webgl-examples/tutorial/sample1",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample1/index.html$",
        "http://mdn.github.io/webgl-examples/tutorial/sample1/index.html",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample1/webgl-demo.js$",
        "http://mdn.github.io/webgl-examples/tutorial/sample1/webgl-demo.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample1/webgl.css$",
        "http://mdn.github.io/webgl-examples/tutorial/webgl.css",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample2$",
        "http://mdn.github.io/webgl-examples/tutorial/sample2",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample2/glUtils.js$",
        "http://mdn.github.io/webgl-examples/tutorial/glUtils.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample2/index.html$",
        "http://mdn.github.io/webgl-examples/tutorial/sample2/index.html",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample2/sylvester.js$",
        "http://mdn.github.io/webgl-examples/tutorial/sylvester.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample2/webgl-demo.js$",
        "http://mdn.github.io/webgl-examples/tutorial/sample2/webgl-demo.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample2/webgl.css$",
        "http://mdn.github.io/webgl-examples/tutorial/webgl.css",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample3$",
        "http://mdn.github.io/webgl-examples/tutorial/sample3",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample3/glUtils.js$",
        "http://mdn.github.io/webgl-examples/tutorial/glUtils.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample3/index.html$",
        "http://mdn.github.io/webgl-examples/tutorial/sample3/index.html",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample3/sylvester.js$",
        "http://mdn.github.io/webgl-examples/tutorial/sylvester.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample3/webgl-demo.js$",
        "http://mdn.github.io/webgl-examples/tutorial/sample3/webgl-demo.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample3/webgl.css$",
        "http://mdn.github.io/webgl-examples/tutorial/webgl.css",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample4$",
        "http://mdn.github.io/webgl-examples/tutorial/sample4",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample4/glUtils.js$",
        "http://mdn.github.io/webgl-examples/tutorial/glUtils.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample4/index.html$",
        "http://mdn.github.io/webgl-examples/tutorial/sample4/index.html",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample4/sylvester.js$",
        "http://mdn.github.io/webgl-examples/tutorial/sylvester.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample4/webgl-demo.js$",
        "http://mdn.github.io/webgl-examples/tutorial/sample4/webgl-demo.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample4/webgl.css$",
        "http://mdn.github.io/webgl-examples/tutorial/webgl.css",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample5$",
        "http://mdn.github.io/webgl-examples/tutorial/sample5",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample5/glUtils.js$",
        "http://mdn.github.io/webgl-examples/tutorial/glUtils.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample5/index.html$",
        "http://mdn.github.io/webgl-examples/tutorial/sample5/index.html",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample5/sylvester.js$",
        "http://mdn.github.io/webgl-examples/tutorial/sylvester.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample5/webgl-demo.js$",
        "http://mdn.github.io/webgl-examples/tutorial/sample5/webgl-demo.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample5/webgl.css$",
        "http://mdn.github.io/webgl-examples/tutorial/webgl.css",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample6$",
        "http://mdn.github.io/webgl-examples/tutorial/sample6",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample6/cubetexture.png$",
        "http://mdn.github.io/webgl-examples/tutorial/sample6/cubetexture.png",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample6/glUtils.js$",
        "http://mdn.github.io/webgl-examples/tutorial/glUtils.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample6/index.html$",
        "http://mdn.github.io/webgl-examples/tutorial/sample6/index.html",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample6/sylvester.js$",
        "http://mdn.github.io/webgl-examples/tutorial/sylvester.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample6/webgl-demo.js$",
        "http://mdn.github.io/webgl-examples/tutorial/sample6/webgl-demo.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample6/webgl.css$",
        "http://mdn.github.io/webgl-examples/tutorial/webgl.css",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample7$",
        "http://mdn.github.io/webgl-examples/tutorial/sample7",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample7/cubetexture.png$",
        "http://mdn.github.io/webgl-examples/tutorial/sample7/cubetexture.png",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample7/glUtils.js$",
        "http://mdn.github.io/webgl-examples/tutorial/glUtils.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample7/index.html$",
        "http://mdn.github.io/webgl-examples/tutorial/sample7/index.html",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample7/sylvester.js$",
        "http://mdn.github.io/webgl-examples/tutorial/sylvester.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample7/webgl-demo.js$",
        "http://mdn.github.io/webgl-examples/tutorial/sample7/webgl-demo.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample7/webgl.css$",
        "http://mdn.github.io/webgl-examples/tutorial/webgl.css",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample8$",
        "http://mdn.github.io/webgl-examples/tutorial/sample8",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample8/Firefox.ogv$",
        "http://mdn.github.io/webgl-examples/tutorial/sample8/Firefox.ogv",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample8/glUtils.js$",
        "http://mdn.github.io/webgl-examples/tutorial/glUtils.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample8/index.html$",
        "http://mdn.github.io/webgl-examples/tutorial/sample8/index.html",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample8/sylvester.js$",
        "http://mdn.github.io/webgl-examples/tutorial/sylvester.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample8/webgl-demo.js$",
        "http://mdn.github.io/webgl-examples/tutorial/sample8/webgl-demo.js",
        re_flags="i",
        permanent=True,
    ),
    redirect(
        r"^samples/webgl/sample8/webgl.css$",
        "http://mdn.github.io/webgl-examples/tutorial/webgl.css",
        re_flags="i",
        permanent=True,
    ),
    # All of the remaining "samples/" URL's are redirected to the
    # the media domain (ATTACHMENTS_AWS_S3_CUSTOM_DOMAIN).
    redirect(
        r"^samples/(?P<sample_path>.*)$",
        f"{settings.ATTACHMENTS_AWS_S3_CUSTOM_URL}/samples/{{sample_path}}",
        re_flags="i",
        permanent=False,
    ),
    # Bug 887428 - Misprinted URL in promo materials
    # RewriteRule ^Firefox_OS/Security$ docs/Mozilla/Firefox_OS/Security
    # [R=301,L,NC]
    redirect(
        r"^Firefox_OS/Security$",
        "/docs/Mozilla/Firefox_OS/Security",
        re_flags="i",
        permanent=True,
    ),
    # Old landing pages. The regex, adapted from Bedrock, captures locale prefixes.
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?mobile/?$ /$1docs/Mozilla/Mobile
    # [R=301,L]
    locale_redirect(r"^?mobile/?$", "/docs/Mozilla/Mobile", permanent=True),
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?addons/?$ /$1Add-ons [R=301,L]
    locale_redirect(r"^?addons/?$", "/Add-ons", permanent=True),
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?mozilla/?$ /$1docs/Mozilla [R=301,L]
    locale_redirect(r"^?mozilla/?$", "/docs/Mozilla", permanent=True),
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?web/?$ /$1docs/Web [R=301,L]
    locale_redirect(r"^?web/?$", "/docs/Web", permanent=True),
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?learn/html5/?$
    # /$1docs/Web/Guide/HTML/HTML5 [R=301,L]
    locale_redirect(r"^?learn/html5/?$", "/docs/Web/Guide/HTML/HTML5", permanent=True),
    # Some blanket section moves / renames
    # RewriteRule ^En/JavaScript/Reference/Objects/Array$
    # en-US/docs/JavaScript/Reference/Global_Objects/Array [R=301,L,NC]
    redirect(
        r"^En/JavaScript/Reference/Objects/Array$",
        "/en-US/docs/JavaScript/Reference/Global_Objects/Array",
        re_flags="i",
        permanent=True,
    ),
    # RewriteRule ^En/JavaScript/Reference/Objects$
    # en-US/docs/JavaScript/Reference/Global_Objects/Object [R=301,L,NC]
    redirect(
        r"^En/JavaScript/Reference/Objects$",
        "/en-US/docs/JavaScript/Reference/Global_Objects/Object",
        re_flags="i",
        permanent=True,
    ),
    # RewriteRule ^En/Core_JavaScript_1\.5_Reference/Objects/(.*)
    # en-US/docs/JavaScript/Reference/Global_Objects/$1 [R=301,L,NC]
    redirect(
        r"^En/Core_JavaScript_1\.5_Reference/Objects/(?P<suffix>.*)$",
        "/en-US/docs/JavaScript/Reference/Global_Objects/{suffix}",
        re_flags="i",
        permanent=True,
    ),
    # RewriteRule ^En/Core_JavaScript_1\.5_Reference/(.*)
    # en-US/docs/JavaScript/Reference/$1 [R=301,L,NC]
    redirect(
        r"^En/Core_JavaScript_1\.5_Reference/(?P<suffix>.*)$",
        "/en-US/docs/JavaScript/Reference/{suffix}",
        re_flags="i",
        permanent=True,
    ),
    # RewriteRule ^([\w\-]*)/HTML5$ $1/docs/HTML/HTML5 [R=301,L,NC]
    locale_redirect(r"^HTML5$", "/docs/HTML/HTML5", re_flags="i", permanent=True),
    # RewriteRule web-tech/2008/09/12/css-transforms
    # /docs/CSS/Using_CSS_transforms [R=301,L]
    redirect(
        r"^web-tech/2008/09/12/css-transforms$",
        "/docs/CSS/Using_CSS_transforms",
        permanent=True,
    ),
    # RewriteRule ^([\w\-]*)/docs/?$ $1/docs/Web [R=301,L,NC]
    locale_redirect(r"^/docs/?$", "/docs/Web", re_flags="i", permanent=True),
    # DevNews
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?devnews/index.php/feed.*
    # https://blog.mozilla.org/feed/ [R=301,L]
    locale_redirect(
        r"^?devnews/index.php/feed.*",
        "https://blog.mozilla.org/feed/",
        prepend_locale=False,
        permanent=True,
    ),
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?devnews.*
    # https://wiki.mozilla.org/Releases [R=301,L]
    locale_redirect(
        r"?devnews.*",
        "https://wiki.mozilla.org/Releases",
        prepend_locale=False,
        permanent=True,
    ),
    # Old "Learn" pages
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?learn/html /$1Learn/HTML [R=301,L]
    locale_redirect(
        r"?learn/html",
        # TODO: new path '/docs/Learn/HTML',
        "/Learn/HTML",
        permanent=True,
    ),
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?learn/css /$1Learn/CSS [R=301,L]
    locale_redirect(
        r"?learn/css",
        # TODO: new path '/docs/Learn/CSS',
        "/Learn/CSS",
        permanent=True,
    ),
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?learn/javascript /$1Learn/JavaScript
    # [R=301,L]
    locale_redirect(
        r"^?learn/javascript",
        # TODO: new path '/docs/Learn/JavaScript',
        "/Learn/JavaScript",
        permanent=True,
    ),
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?learn /$1Learn [R=301,L]
    locale_redirect(
        r"^?learn",
        # TODO: new path '/docs/Learn',
        "/Learn",
        permanent=True,
    ),
    # BananaBread demo (bug 1238041)
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?demos/detail/bananabread$
    # https://github.com/kripken/BananaBread/ [R=301,L]
    locale_redirect(
        r"^?demos/detail/bananabread$",
        "https://github.com/kripken/BananaBread/",
        prepend_locale=False,
        permanent=True,
    ),
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?demos/detail/bananabread/launch$
    # https://kripken.github.io/BananaBread/cube2/index.html [R=301,L]
    locale_redirect(
        r"^?demos/detail/bananabread/launch$",
        "https://kripken.github.io/BananaBread/cube2/index.html",
        prepend_locale=False,
        permanent=True,
    ),
    # All other Demo Studio and Dev Derby paths (bug 1238037)
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?demos
    # /$1docs/Web/Demos_of_open_web_technologies? [R=301,L]
    locale_redirect(
        r"^?demos", "/docs/Web/Demos_of_open_web_technologies", permanent=True
    ),
    # Legacy off-site redirects (bug 1362438)
    # RewriteRule ^contests/ http://www.mozillalabs.com/ [R=302,L]
    redirect(r"^contests", "http://www.mozillalabs.com/", permanent=False),
    # RewriteRule ^es4 http://www.ecma-international.org/memento/TC39.htm [R=302,L]
    redirect(
        r"^es4", "http://www.ecma-international.org/memento/TC39.htm", permanent=False
    ),
]

zone_redirects = (
    (
        "Add-ons",
        "Mozilla/Add-ons",
        (
            "ar",
            "bn",
            "ca",
            "de",
            "en-US",
            "es",
            "fa",
            "fr",
            "hu",
            "id",
            "it",
            "ja",
            "ms",
            "nl",
            "pl",
            "pt-BR",
            "pt-PT",
            "ru",
            "sv-SE",
            "th",
            "uk",
            "vi",
            "zh-CN",
            "zh-TW",
            None,
        ),
    ),
    ("Add-ons", "Mozilla/Πρόσθετα", ("el",)),
    ("Add-ons", "Mozilla/애드온들", ("ko",)),
    ("Add-ons", "Mozilla/Eklentiler", ("tr",)),
    (
        "Firefox",
        "Mozilla/Firefox",
        (
            "ar",
            "bm",
            "ca",
            "de",
            "el",
            "en-US",
            "es",
            "fi",
            "fr",
            "he",
            "hi-IN",
            "hu",
            "id",
            "it",
            "ja",
            "ko",
            "ms",
            "my",
            "nl",
            "pl",
            "pt-BR",
            "pt-PT",
            "ru",
            "sv-SE",
            "th",
            "tr",
            "vi",
            "zh-CN",
            "zh-TW",
            None,
        ),
    ),
    ("Firefox", "Mozilla/ফায়ারফক্স", ("bn",)),
    ("Apps", "Web/Apps", ("en-US", "fa", "fr", "ja", "th", "zh-CN", "zh-TW", None)),
    ("Apps", "Web/Aplicaciones", ("es",)),
    ("Apps", "Apps", ("bn", "de", "it", "ko", "pt-BR", "ru")),
    ("Learn", "Learn", ("ca", "de", None)),
    ("Apprendre", "Apprendre", ("fr",)),
    (
        "Marketplace",
        "Mozilla/Marketplace",
        ("de", "en-US", "es", "fr", "it", "ja", "zh-CN", None),
    ),
    ("Marketplace", "Mozilla/بازار", ("fa",)),
)

zone_pattern_fmt = r"^{prefix}{zone_root_pattern}(?:/?|(?P<sub_path>[/$].+))$"
sub_path_fmt = "/{prefix}docs/{wiki_slug}{{sub_path}}"

zone_redirectpatterns = []
for zone_root, wiki_slug, locales in zone_redirects:
    for locale in locales:
        zone_root_pattern = zone_root
        if zone_root != wiki_slug:
            zone_root_pattern = "(?:docs/)?" + zone_root_pattern
        # NOTE: The redirect for the case when there is no locale for a zone
        # must be handled here, because if we let LocaleMiddleware handle the
        # 404 response and redirect to the proper locale, the path would be
        # considered invalid.
        prefix = (locale + "/") if locale else ""
        pattern = zone_pattern_fmt.format(
            prefix=prefix, zone_root_pattern=zone_root_pattern
        )
        sub_path = sub_path_fmt.format(prefix=prefix, wiki_slug=wiki_slug)
        zone_redirectpatterns.append(
            redirect(
                pattern,
                sub_path,
                permanent=False,
                decorators=shared_cache_control_for_zones,
            )
        )

marionette_client_docs_url = "https://marionette-client.readthedocs.io/en/latest/"
marionette_docs_root_url = (
    "https://firefox-source-docs.mozilla.org/testing/marionette/marionette/"
)
external_redirect = partial(
    locale_redirect, re_flags="i", prepend_locale=False, permanent=True
)

marionette_redirectpatterns = [
    external_redirect(
        r"docs/(?:Mozilla/QA/)?Marionette$", marionette_docs_root_url + "index.html"
    ),
    external_redirect(
        r"docs/(?:Mozilla/QA/)?Marionette/Builds$",
        marionette_docs_root_url + "Building.html",
    ),
    external_redirect(
        r"docs/(?:Mozilla/QA/)?Marionette/Client$", marionette_client_docs_url
    ),
    external_redirect(
        r"docs/Mozilla/QA/Marionette/Python_Client$", marionette_client_docs_url
    ),
    external_redirect(
        r"docs/(?:Mozilla/QA/)?Marionette/Developer_setup$",
        marionette_docs_root_url + "Contributing.html",
    ),
    external_redirect(
        r"docs/Marionette_Test_Runner$", marionette_docs_root_url + "PythonTests.html"
    ),
    external_redirect(
        r"docs/Mozilla/QA/Marionette/Marionette_Test_Runner$",
        marionette_docs_root_url + "PythonTests.html",
    ),
    external_redirect(
        r"docs/(?:Mozilla/QA/)?Marionette/(?:MarionetteTestCase"
        r"|Marionette_Python_Tests|Running_Tests|Tests)$",
        marionette_docs_root_url + "PythonTests.html",
    ),
    external_redirect(
        r"docs/Mozilla/QA/Marionette/Protocol$",
        marionette_docs_root_url + "Protocol.html",
    ),
    external_redirect(
        r"docs/Mozilla/QA/Marionette/WebDriver/status$",
        "https://bugzilla.mozilla.org"
        "/showdependencytree.cgi?id=721859&hide_resolved=1",
    ),
    external_redirect(
        r"docs/Marionette/Debugging$", marionette_docs_root_url + "Debugging.html"
    ),
]

webextensions_redirectpatterns = [
    external_redirect(
        r"docs/Mozilla/Add-ons/{}$".format(ao_path),
        "https://extensionworkshop.com/documentation/" + ew_path,
    )
    for ao_path, ew_path in (
        ("WebExtensions/Security_best_practices", "develop/build-a-secure-extension/"),
        (
            "WebExtensions/user_interface/Accessibility_guidelines",
            "develop/build-an-accessible-extension/",
        ),
        (
            "WebExtensions/onboarding_upboarding_offboarding_best_practices",
            "develop/onboard-upboard-offboard-users/",
        ),
        (
            "WebExtensions/Porting_a_Google_Chrome_extension",
            "develop/porting-a-google-chrome-extension/",
        ),
        (
            "WebExtensions/Porting_a_legacy_Firefox_add-on",
            "develop/porting-a-legacy-firefox-extension/",
        ),
        (
            "WebExtensions/Comparison_with_the_Add-on_SDK",
            "develop/comparison-with-the-add-on-sdk/",
        ),
        (
            "WebExtensions/Comparison_with_XUL_XPCOM_extensions",
            "develop/comparison-with-xul-xpcom-extensions/",
        ),
        (
            "WebExtensions/Differences_between_desktop_and_Android",
            "develop/differences-between-desktop-and-android-extensions/",
        ),
        (
            "WebExtensions/Development_Tools",
            "develop/browser-extension-development-tools/",
        ),
        (
            "WebExtensions/Choose_a_Firefox_version_for_web_extension_develop",
            "develop/choosing-a-firefox-version-for-extension-development/",
        ),
        (
            "WebExtensions/User_experience_best_practices",
            "develop/user-experience-best-practices/",
        ),
        (
            "WebExtensions/Prompt_users_for_data_and_privacy_consents",
            "develop/best-practices-for-collecting-user-data-consents/",
        ),
        (
            "WebExtensions/Temporary_Installation_in_Firefox",
            "develop/temporary-installation-in-firefox/",
        ),
        ("WebExtensions/Debugging", "develop/debugging/"),
        (
            "WebExtensions/Testing_persistent_and_restart_features",
            "develop/testing-persistent-and-restart-features/",
        ),
        ("WebExtensions/Test_permission_requests", "develop/test-permission-requests/"),
        (
            "WebExtensions/Developing_WebExtensions_for_Firefox_for_Android",
            "develop/developing-extensions-for-firefox-for-android/",
        ),
        (
            "WebExtensions/Getting_started_with_web-ext",
            "develop/getting-started-with-web-ext/",
        ),
        (
            "WebExtensions/web-ext_command_reference",
            "develop/web-ext-command-reference/",
        ),
        (
            "WebExtensions/WebExtensions_and_the_Add-on_ID",
            "develop/extensions-and-the-add-on-id/",
        ),
        (
            "WebExtensions/Request_the_right_permissions",
            "develop/request-the-right-permissions/",
        ),
        (
            "WebExtensions/Best_practices_for_updating_your_extension",
            "manage/best-practices-for-updating/",
        ),
        ("Updates", "manage/updating-your-extension/"),
        (
            "WebExtensions/Distribution_options",
            "publish/signing-and-distribution-overview/",
        ),
        (
            "Themes/Using_the_AMO_theme_generator",
            "themes/using-the-amo-theme-generator/",
        ),
        ("WebExtensions/Developer_accounts", "publish/developer-accounts/"),
        (
            "Distribution",
            "publish/signing-and-distribution-overview/#distributing-your-addon",
        ),
        ("WebExtensions/Package_your_extension_", "publish/package-your-extension/"),
        ("Distribution/Submitting_an_add-on", "publish/submitting-an-add-on/"),
        ("Source_Code_Submission", "publish/source-code-submission/"),
        ("Distribution/Resources_for_publishers", "manage/resources-for-publishers/"),
        ("Listing", "develop/create-an-appealing-listing/"),
        (
            "Distribution/Make_money_from_browser_extensions",
            "publish/make-money-from-browser-extensions/",
        ),
        (
            "Distribution/Promoting_your_extension_or_theme",
            "publish/promoting-your-extension/",
        ),
        ("AMO/Policy/Reviews", "publish/add-on-policies/"),
        ("AMO/Policy/Agreement", "publish/firefox-add-on-distribution-agreement/"),
        ("Distribution/Retiring_your_extension", "manage/retiring-your-extension/"),
        (
            "WebExtensions/Distribution_options/Sideloading_add-ons",
            "publish/distribute-sideloading/",
        ),
        (
            "WebExtensions/Distribution_options/Add-ons_for_desktop_apps",
            "publish/distribute-for-desktop-apps/",
        ),
        ("WebExtensions/Distribution_options/Add-ons_in_the_enterprise", "enterprise/"),
        ("AMO/Blocking_Process", "publish/add-ons-blocking-process/"),
        ("Third_Party_Library_Usage", "publish/third-party-library-usage/"),
        (
            "WebExtensions/What_does_review_rejection_mean_to_users",
            "publish/what-does-review-rejection-mean-to-users/",
        ),
        ("AMO/Policy/Featured", "publish/recommended-extensions/"),
    )
]

redirectpatterns = (
    scl3_redirectpatterns
    + zone_redirectpatterns
    + marionette_redirectpatterns
    + webextensions_redirectpatterns
    + [
        locale_redirect(
            r"^fellowship", "/docs/Archive/2015_MDN_Fellowship_Program", permanent=True
        ),
    ]
)
