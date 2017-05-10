from redirect_urls import redirect

# Redirects/rewrites/aliases migrated from SCL3 httpd config
redirectpatterns = [
    # RewriteRule ^/media/(redesign/)?css/(.*)-min.css$
    # /static/build/styles/$2.css [L,R=301]
    redirect(r'^media/(?:redesign/)?css/(?P<doc>.*)-min.css$',
             '/static/build/styles/{doc}.css',
             prepend_locale=False, permanent=True),

    # RewriteRule ^/media/(redesign/)?js/(.*)-min.js$ /static/build/js/$2.js
    # [L,R=301]
    redirect(r'^media/(?:redesign/)?js/(?P<doc>.*)-min.js$',
             '/static/build/js/{doc}.js',
             prepend_locale=False, permanent=True),

    # RewriteRule ^/media/(redesign/)?img(.*) /static/img$2 [L,R=301]
    redirect(r'^media/(?:redesign/)?img(?P<suffix>.*)$',
             '/static/img{suffix}',
             prepend_locale=False, permanent=True),

    # RewriteRule ^/media/(redesign/)?css(.*) /static/styles$2 [L,R=301]
    redirect(r'^media/(?:redesign/)?css(?P<suffix>.*)$',
             '/static/styles{suffix}',
             prepend_locale=False, permanent=True),

    # RewriteRule ^/media/(redesign/)?js(.*) /static/js$2 [L,R=301]
    redirect(r'^media/(?:redesign/)?js(?P<suffix>.*)$',
             '/static/js{suffix}',
             prepend_locale=False, permanent=True),

    # RewriteRule ^/media/(redesign/)?fonts(.*) /static/fonts$2 [L,R=301]
    redirect(r'^media/(?:redesign/)?fonts(?P<suffix>.*)$',
             '/static/fonts{suffix}',
             prepend_locale=False, permanent=True),

    # RedirectMatch 302 /media/uploads/demos/(.*)$
    # https://developer.mozilla.org/docs/Web/Demos_of_open_web_technologies/
    # Note that this has prepend_locale=True
    redirect(r'^media/uploads/demos/(?:.*)$',
             '/docs/Web/Demos_of_open_web_technologies/',
             prepend_locale=True, permanent=False),

    # RewriteRule ^(.*)//(.*)//(.*)$ $1_$2_$3 [R=301,L,NC]
    # Note that this has prepend_locale=True
    redirect(r'^(?P<one>.*)//(?P<two>.*)//(?P<three>.*)$',
             '/{one}_{two}_{three}',
             re_flags='i', prepend_locale=True, permanent=True),

    # RewriteRule ^(.*)//(.*)$ $1_$2 [R=301,L,NC]
    # Note that this has prepend_locale=True
    redirect(r'^(?P<one>.*)//(?P<two>.*)$',
             '/{one}_{two}',
             re_flags='i', prepend_locale=True, permanent=True),

    # The remaining redirects don't show explicit RewriteRule as comments,
    # as they're all in the style of "static URL A now points at static URL B"

    # Bug 1078186 - Redirect old static canvas examples to wiki pages
    # canvas tutorial
    redirect(
        r'^samples/canvas-tutorial/2_1_canvas_rect.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Rectangular_shape_example',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/2_2_canvas_moveto.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Moving_the_pen',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/2_3_canvas_lineto.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Lines',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/2_4_canvas_arc.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Arcs',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/2_5_canvas_quadraticcurveto.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Quadratic_Bezier_curves',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/2_6_canvas_beziercurveto.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Cubic_Bezier_curves',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/3_1_canvas_drawimage.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Using_images#Drawing_images',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/3_2_canvas_drawimage.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Using_images#Example.3A_Tiling_an_image',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/3_3_canvas_drawimage.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Using_images#Example.3A_Framing_an_image',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/3_4_canvas_gallery.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Using_images#Art_gallery_example',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_1_canvas_fillstyle.html$',
        '/docs/Web/API/CanvasRenderingContext2D.fillStyle',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_2_canvas_strokestyle.html$',
        '/docs/Web/API/CanvasRenderingContext2D.strokeStyle',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_3_canvas_globalalpha.html$',
        '/docs/Web/API/CanvasRenderingContext2D.globalAlpha',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_4_canvas_rgba.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#An_example_using_rgba()',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_5_canvas_linewidth.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_lineWidth_example',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_6_canvas_linecap.html$',
        '/docs/Web/API/CanvasRenderingContext2D.lineCap',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_7_canvas_linejoin.html$',
        '/docs/Web/API/CanvasRenderingContext2D.lineJoin',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_8_canvas_miterlimit.html$',
        '/docs/Web/API/CanvasRenderingContext2D.miterLimit',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_9_canvas_lineargradient.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_createLinearGradient_example',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_10_canvas_radialgradient.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_createRadialGradient_example',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/4_11_canvas_createpattern.html$',
        '/docs/Web/API/CanvasRenderingContext2D.createPattern',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/5_1_canvas_savestate.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Transformations#A_save_and_restore_canvas_state_example',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/5_2_canvas_translate.html$',
        '/docs/Web/API/CanvasRenderingContext2D.translate',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/5_3_canvas_rotate.html$',
        '/docs/Web/API/CanvasRenderingContext2D.rotate',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/5_4_canvas_scale.html$',
        '/docs/Web/API/CanvasRenderingContext2D.scale',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/6_1_canvas_composite.html$',
        '/docs/Web/API/CanvasRenderingContext2D.globalCompositeOperation',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/6_2_canvas_clipping.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Compositing#Clipping_paths',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/globalCompositeOperation.html$',
        '/docs/Web/API/CanvasRenderingContext2D.globalCompositeOperation',
        re_flags='i', prepend_locale=False, permanent=True),

    ##################################
    # MOZILLADEMOS
    ##################################
    # canvas images
    redirect(
        r'^samples/canvas-tutorial/images/backdrop.png$',
        'https://mdn.mozillademos.org/files/5395/backdrop.png',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/bg_gallery.png$',
        'https://mdn.mozillademos.org/files/5415/bg_gallery.png',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_1.jpg$',
        'https://mdn.mozillademos.org/files/5399/gallery_1.jpg',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_2.jpg$',
        'https://mdn.mozillademos.org/files/5401/gallery_2.jpg',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_3.jpg$',
        'https://mdn.mozillademos.org/files/5403/gallery_3.jpg',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_4.jpg$',
        'https://mdn.mozillademos.org/files/5405/gallery_4.jpg',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_5.jpg$',
        'https://mdn.mozillademos.org/files/5407/gallery_5.jpg',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_6.jpg$',
        'https://mdn.mozillademos.org/files/5409/gallery_6.jpg',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_7.jpg$',
        'https://mdn.mozillademos.org/files/5411/gallery_7.jpg',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/gallery_8.jpg$',
        'https://mdn.mozillademos.org/files/5413/gallery_8.jpg',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/picture_frame.png$',
        'https://mdn.mozillademos.org/files/242/Canvas_picture_frame.png',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/rhino.jpg$',
        'https://mdn.mozillademos.org/files/5397/rhino.jpg',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/canvas-tutorial/images/wallpaper.png$',
        'https://mdn.mozillademos.org/files/222/Canvas_createpattern.png',
        re_flags='i', prepend_locale=False, permanent=True),

    # canvas example in samples/domref
    redirect(
        r'^samples/domref/mozGetAsFile.html$',
        '/docs/Web/API/HTMLCanvasElement.mozGetAsFile',
        re_flags='i', prepend_locale=False, permanent=True),


    ##################################
    # MDN.GITHUB.IO
    ##################################
    # canvas raycaster
    redirect(
        r'^samples/raycaster/input.js$',
        'http://mdn.github.io/canvas-raycaster/input.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/raycaster/Level.js$',
        'http://mdn.github.io/canvas-raycaster/Level.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/raycaster/Player.js$',
        'http://mdn.github.io/canvas-raycaster/Player.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/raycaster/RayCaster.html$',
        'http://mdn.github.io/canvas-raycaster/index.html',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/raycaster/RayCaster.js$',
        'http://mdn.github.io/canvas-raycaster/RayCaster.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/raycaster/trace.css$',
        'http://mdn.github.io/canvas-raycaster/trace.css',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/raycaster/trace.js$',
        'http://mdn.github.io/canvas-raycaster/trace.js',
        re_flags='i', prepend_locale=False, permanent=True),


    # Bug 1215255 - Redirect static WebGL examples
    redirect(
        r'^samples/webgl/sample1$',
        'http://mdn.github.io/webgl-examples/tutorial/sample1',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample1/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample1/index.html',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample1/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample1/webgl-demo.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample1/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample2$',
        'http://mdn.github.io/webgl-examples/tutorial/sample2',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample2/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample2/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample2/index.html',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample2/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample2/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample2/webgl-demo.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample2/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample3$',
        'http://mdn.github.io/webgl-examples/tutorial/sample3',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample3/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample3/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample3/index.html',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample3/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample3/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample3/webgl-demo.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample3/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample4$',
        'http://mdn.github.io/webgl-examples/tutorial/sample4',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample4/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample4/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample4/index.html',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample4/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample4/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample4/webgl-demo.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample4/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample5$',
        'http://mdn.github.io/webgl-examples/tutorial/sample5',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample5/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample5/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample5/index.html',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample5/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample5/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample5/webgl-demo.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample5/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample6$',
        'http://mdn.github.io/webgl-examples/tutorial/sample6',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample6/cubetexture.png$',
        'http://mdn.github.io/webgl-examples/tutorial/sample6/cubetexture.png',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample6/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample6/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample6/index.html',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample6/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample6/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample6/webgl-demo.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample6/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample7$',
        'http://mdn.github.io/webgl-examples/tutorial/sample7',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample7/cubetexture.png$',
        'http://mdn.github.io/webgl-examples/tutorial/sample7/cubetexture.png',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample7/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample7/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample7/index.html',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample7/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample7/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample7/webgl-demo.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample7/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample8$',
        'http://mdn.github.io/webgl-examples/tutorial/sample8',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample8/Firefox.ogv$',
        'http://mdn.github.io/webgl-examples/tutorial/sample8/Firefox.ogv',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample8/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample8/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample8/index.html',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample8/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample8/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample8/webgl-demo.js',
        re_flags='i', prepend_locale=False, permanent=True),

    redirect(
        r'^samples/webgl/sample8/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        re_flags='i', prepend_locale=False, permanent=True),

    # Bug 887428 - Misprinted URL in promo materials
    # RewriteRule ^Firefox_OS/Security$ docs/Mozilla/Firefox_OS/Security
    # [R=301,L,NC]
    redirect(
        r'^Firefox_OS/Security$',
        '/docs/Mozilla/Firefox_OS/Security',
        re_flags='i', prepend_locale=False, permanent=True),

    # Old landing pages. The regex, adapted from Bedrock, captures locale prefixes.
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?mobile/?$ /$1docs/Mozilla/Mobile
    # [R=301,L]
    redirect(
        r'^(?P<localeprefix>\w{2,3}(?:-\w{2})?/)?mobile/?$',
        '/{localeprefix}docs/Mozilla/Mobile',
        prepend_locale=True, permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?addons/?$ /$1Add-ons [R=301,L]
    redirect(
        r'^(?P<localeprefix>\w{2,3}(?:-\w{2})?/)?addons/?$',
        '/{localeprefix}Add-ons',
        prepend_locale=True, permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?mozilla/?$ /$1docs/Mozilla [R=301,L]
    redirect(
        r'^(?P<localeprefix>\w{2,3}(?:-\w{2})?/)?mozilla/?$',
        '/{localeprefix}docs/Mozilla',
        prepend_locale=True, permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?web/?$ /$1docs/Web [R=301,L]
    redirect(
        r'^(?P<localeprefix>\w{2,3}(?:-\w{2})?/)?web/?$',
        '/{localeprefix}docs/Web',
        prepend_locale=True, permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?learn/html5/?$
    # /$1docs/Web/Guide/HTML/HTML5 [R=301,L]
    redirect(
        r'^(?P<localeprefix>\w{2,3}(?:-\w{2})?/)?learn/html5/?$',
        '/{localeprefix}docs/Web/Guide/HTML/HTML5',
        prepend_locale=True, permanent=True),

    # Some blanket section moves / renames
    # RewriteRule ^En/JavaScript/Reference/Objects/Array$
    # en-US/docs/JavaScript/Reference/Global_Objects/Array [R=301,L,NC]
    redirect(
        r'^En/JavaScript/Reference/Objects/Array$',
        '/en-US/docs/JavaScript/Reference/Global_Objects/Array',
        re_flags='i', prepend_locale=True, permanent=True),

    # RewriteRule ^En/JavaScript/Reference/Objects$
    # en-US/docs/JavaScript/Reference/Global_Objects/Object [R=301,L,NC]
    redirect(
        r'^En/JavaScript/Reference/Objects$',
        '/en-US/docs/JavaScript/Reference/Global_Objects/Object',
        re_flags='i', prepend_locale=True, permanent=True),

    # RewriteRule ^En/Core_JavaScript_1\.5_Reference/Objects/(.*)
    # en-US/docs/JavaScript/Reference/Global_Objects/$1 [R=301,L,NC]
    redirect(
        r'^En/Core_JavaScript_1\.5_Reference/Objects/(?P<suffix>.*)$',
        '/en-US/docs/JavaScript/Reference/Global_Objects/{suffix}',
        re_flags='i', prepend_locale=True, permanent=True),

    # RewriteRule ^En/Core_JavaScript_1\.5_Reference/(.*)
    # en-US/docs/JavaScript/Reference/$1 [R=301,L,NC]
    redirect(
        r'^En/Core_JavaScript_1\.5_Reference/(?P<suffix>.*)$',
        '/en-US/docs/JavaScript/Reference/{suffix}',
        re_flags='i', prepend_locale=True, permanent=True),

    # RewriteRule ^([\w\-]*)/HTML5$ $1/docs/HTML/HTML5 [R=301,L,NC]
    redirect(
        r'^(?P<pre>[\w\-]*)/HTML5$',
        '/{pre}/docs/HTML/HTML5',
        re_flags='i', prepend_locale=False, permanent=True),

    # RewriteRule web-tech/2008/09/12/css-transforms
    # /docs/CSS/Using_CSS_transforms [R=301,L]
    redirect(
        r'^web-tech/2008/09/12/css-transforms$',
        '/docs/CSS/Using_CSS_transforms',
        prepend_locale=False, permanent=True),

    # RewriteRule ^([\w\-]*)/docs/?$ $1/docs/Web [R=301,L,NC]
    redirect(
        r'^(?P<pre>[\w\-]*)/docs/?$',
        '/{pre}/docs/Web',
        re_flags='i', prepend_locale=False, permanent=True),

    # DevNews
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?devnews/index.php/feed.*
    # https://blog.mozilla.org/feed/ [R=301,L]
    redirect(
        r'^(\w{2,3}(?:-\w{2})?/)?devnews/index.php/feed.*',
        'https://blog.mozilla.org/feed/',
        prepend_locale=False, permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?devnews.*
    # https://wiki.mozilla.org/Releases [R=301,L]
    redirect(
        r'(\w{2,3}(?:-\w{2})?/)?devnews.*',
        'https://wiki.mozilla.org/Releases',
        prepend_locale=False, permanent=True),

    # Old "Learn" pages
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?learn/html /$1Learn/HTML [R=301,L]
    redirect(
        r'^(?P<pre>\w{2,3}(?:-\w{2})?/)?learn/html',
        '/{pre}Learn/HTML',
        prepend_locale=True, permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?learn/css /$1Learn/CSS [R=301,L]
    redirect(
        r'^(?P<pre>\w{2,3}(?:-\w{2})?/)?learn/css',
        '/{pre}Learn/CSS',
        prepend_locale=True, permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?learn/javascript /$1Learn/JavaScript
    # [R=301,L]
    redirect(
        r'^(?P<pre>\w{2,3}(?:-\w{2})?/)?learn/javascript',
        '/{pre}Learn/JavaScript',
        prepend_locale=True, permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?learn /$1Learn [R=301,L]
    redirect(
        r'^(?P<pre>\w{2,3}(?:-\w{2})?/)?learn',
        '/{pre}Learn',
        prepend_locale=True, permanent=True),

    # BananaBread demo (bug 1238041)
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?demos/detail/bananabread$
    # https://github.com/kripken/BananaBread/ [R=301,L]
    redirect(
        r'^(\w{2,3}(?:-\w{2})?/)?demos/detail/bananabread$',
        'https://github.com/kripken/BananaBread/',
        prepend_locale=False, permanent=True),

    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?demos/detail/bananabread/launch$
    # https://kripken.github.io/BananaBread/cube2/index.html [R=301,L]
    redirect(
        r'^(\w{2,3}(?:-\w{2})?/)?demos/detail/bananabread/launch$',
        'https://kripken.github.io/BananaBread/cube2/index.html',
        prepend_locale=False, permanent=True),


    # All other Demo Studio and Dev Derby paths (bug 1238037)
    # RewriteRule ^(\w{2,3}(?:-\w{2})?/)?demos
    # /$1docs/Web/Demos_of_open_web_technologies? [R=301,L]
    redirect(
        r'^(?P<pre>\w{2,3}(?:-\w{2})?/)?demos',
        '/{pre}docs/Web/Demos_of_open_web_technologies',
        prepend_locale=True, permanent=True),
]
