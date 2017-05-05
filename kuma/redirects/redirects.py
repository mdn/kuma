from redirect_urls import redirect

# Redirects/rewrites/aliases migrated from SCL3 httpd config
redirectpatterns = [
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
    redirect(r'^media/uploads/demos/(?:.*)$',
             'https://developer.mozilla.org/docs/Web/Demos_of_open_web_technologies/'),

    # RewriteRule ^(.*)//(.*)$ $1_$2 [R=301,L,NC]
    redirect(r'^(?P<one>.*)//(?P<two>.*)$',
             '{one}_{two}',
             permanent=True),

    # RewriteRule ^(.*)//(.*)//(.*)$ $1_$2_$3 [R=301,L,NC]
    redirect(r'^(?P<one>.*)//(?P<two>.*)//(?P<three>.*)$',
             '{one}_{two}_{three}',
             permanent=True),




    # Bug 1078186 - Redirect old static canvas examples to wiki pages
    # canvas tutorial
    redirect(
        r'^samples/canvas-tutorial/2_1_canvas_rect.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Rectangular_shape_example',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/2_2_canvas_moveto.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Moving_the_pen',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/2_3_canvas_lineto.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Lines',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/2_4_canvas_arc.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Arcs',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/2_5_canvas_quadraticcurveto.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Quadratic_Bezier_curves',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/2_6_canvas_beziercurveto.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Cubic_Bezier_curves',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/3_1_canvas_drawimage.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Using_images#Drawing_images',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/3_2_canvas_drawimage.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Using_images#Example.3A_Tiling_an_image',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/3_3_canvas_drawimage.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Using_images#Example.3A_Framing_an_image',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/3_4_canvas_gallery.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Using_images#Art_gallery_example',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/4_1_canvas_fillstyle.html$',
        '/docs/Web/API/CanvasRenderingContext2D.fillStyle',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/4_2_canvas_strokestyle.html$',
        '/docs/Web/API/CanvasRenderingContext2D.strokeStyle',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/4_3_canvas_globalalpha.html$',
        '/docs/Web/API/CanvasRenderingContext2D.globalAlpha',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/4_4_canvas_rgba.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#An_example_using_rgba()',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/4_5_canvas_linewidth.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_lineWidth_example',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/4_6_canvas_linecap.html$',
        '/docs/Web/API/CanvasRenderingContext2D.lineCap',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/4_7_canvas_linejoin.html$',
        '/docs/Web/API/CanvasRenderingContext2D.lineJoin',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/4_8_canvas_miterlimit.html$',
        '/docs/Web/API/CanvasRenderingContext2D.miterLimit',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/4_9_canvas_lineargradient.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_createLinearGradient_example',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/4_10_canvas_radialgradient.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_createRadialGradient_example',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/4_11_canvas_createpattern.html$',
        '/docs/Web/API/CanvasRenderingContext2D.createPattern',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/5_1_canvas_savestate.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Transformations#A_save_and_restore_canvas_state_example',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/5_2_canvas_translate.html$',
        '/docs/Web/API/CanvasRenderingContext2D.translate',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/5_3_canvas_rotate.html$',
        '/docs/Web/API/CanvasRenderingContext2D.rotate',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/5_4_canvas_scale.html$',
        '/docs/Web/API/CanvasRenderingContext2D.scale',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/6_1_canvas_composite.html$',
        '/docs/Web/API/CanvasRenderingContext2D.globalCompositeOperation',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/6_2_canvas_clipping.html$',
        '/docs/Web/API/Canvas_API/Tutorial/Compositing#Clipping_paths',
        permanent=True),
    # [NE,R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/globalCompositeOperation.html$',
        '/docs/Web/API/CanvasRenderingContext2D.globalCompositeOperation',
        permanent=True),
    # [R=301,L,NC]
    # canvas images
    redirect(
        r'^samples/canvas-tutorial/images/backdrop.png$',
        'https://mdn.mozillademos.org/files/5395/backdrop.png',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/images/bg_gallery.png$',
        'https://mdn.mozillademos.org/files/5415/bg_gallery.png',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/images/gallery_1.jpg$',
        'https://mdn.mozillademos.org/files/5399/gallery_1.jpg',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/images/gallery_2.jpg$',
        'https://mdn.mozillademos.org/files/5401/gallery_2.jpg',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/images/gallery_3.jpg$',
        'https://mdn.mozillademos.org/files/5403/gallery_3.jpg',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/images/gallery_4.jpg$',
        'https://mdn.mozillademos.org/files/5405/gallery_4.jpg',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/images/gallery_5.jpg$',
        'https://mdn.mozillademos.org/files/5407/gallery_5.jpg',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/images/gallery_6.jpg$',
        'https://mdn.mozillademos.org/files/5409/gallery_6.jpg',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/images/gallery_7.jpg$',
        'https://mdn.mozillademos.org/files/5411/gallery_7.jpg',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/images/gallery_8.jpg$',
        'https://mdn.mozillademos.org/files/5413/gallery_8.jpg',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/images/picture_frame.png$',
        'https://mdn.mozillademos.org/files/242/Canvas_picture_frame.png',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/images/rhino.jpg$',
        'https://mdn.mozillademos.org/files/5397/rhino.jpg',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/canvas-tutorial/images/wallpaper.png$',
        'https://mdn.mozillademos.org/files/222/Canvas_createpattern.png',
        permanent=True),
    # [R=301,L,NC]
    # canvas example in samples/domref
    redirect(
        r'^samples/domref/mozGetAsFile.html$',
        '/docs/Web/API/HTMLCanvasElement.mozGetAsFile',
        permanent=True),
    # [R=301,L,NC]

    # canvas raycaster
    redirect(
        r'^samples/raycaster/input.js$',
        'http://mdn.github.io/canvas-raycaster/input.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/raycaster/Level.js$',
        'http://mdn.github.io/canvas-raycaster/Level.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/raycaster/Player.js$',
        'http://mdn.github.io/canvas-raycaster/Player.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/raycaster/RayCaster.html$',
        'http://mdn.github.io/canvas-raycaster/index.html',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/raycaster/RayCaster.js$',
        'http://mdn.github.io/canvas-raycaster/RayCaster.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/raycaster/trace.css$',
        'http://mdn.github.io/canvas-raycaster/trace.css',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/raycaster/trace.js$',
        'http://mdn.github.io/canvas-raycaster/trace.js',
        permanent=True),
    # [R=301,L,NC]

    # Bug 1215255 - Redirect static WebGL examples
    redirect(
        r'^samples/webgl/sample1$',
        'http://mdn.github.io/webgl-examples/tutorial/sample1',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample1/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample1/index.html',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample1/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample1/webgl-demo.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample1/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample2$',
        'http://mdn.github.io/webgl-examples/tutorial/sample2',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample2/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample2/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample2/index.html',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample2/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample2/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample2/webgl-demo.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample2/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample3$',
        'http://mdn.github.io/webgl-examples/tutorial/sample3',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample3/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample3/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample3/index.html',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample3/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample3/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample3/webgl-demo.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample3/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample4$',
        'http://mdn.github.io/webgl-examples/tutorial/sample4',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample4/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample4/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample4/index.html',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample4/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample4/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample4/webgl-demo.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample4/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample5$',
        'http://mdn.github.io/webgl-examples/tutorial/sample5',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample5/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample5/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample5/index.html',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample5/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample5/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample5/webgl-demo.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample5/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample6$',
        'http://mdn.github.io/webgl-examples/tutorial/sample6',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample6/cubetexture.png$',
        'http://mdn.github.io/webgl-examples/tutorial/sample6/cubetexture.png',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample6/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample6/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample6/index.html',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample6/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample6/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample6/webgl-demo.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample6/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample7$',
        'http://mdn.github.io/webgl-examples/tutorial/sample7',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample7/cubetexture.png$',
        'http://mdn.github.io/webgl-examples/tutorial/sample7/cubetexture.png',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample7/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample7/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample7/index.html',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample7/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample7/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample7/webgl-demo.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample7/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample8$',
        'http://mdn.github.io/webgl-examples/tutorial/sample8',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample8/Firefox.ogv$',
        'http://mdn.github.io/webgl-examples/tutorial/sample8/Firefox.ogv',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample8/glUtils.js$',
        'http://mdn.github.io/webgl-examples/tutorial/glUtils.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample8/index.html$',
        'http://mdn.github.io/webgl-examples/tutorial/sample8/index.html',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample8/sylvester.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sylvester.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample8/webgl-demo.js$',
        'http://mdn.github.io/webgl-examples/tutorial/sample8/webgl-demo.js',
        permanent=True),
    # [R=301,L,NC]
    redirect(
        r'^samples/webgl/sample8/webgl.css$',
        'http://mdn.github.io/webgl-examples/tutorial/webgl.css',
        permanent=True),
    # [R=301,L,NC]



]
