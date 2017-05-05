from utils.urls import flatten, url_test

import requests

URLS = flatten((
    url_test("/media/redesign/css/foo-min.css", "/static/build/styles/foo.css"),
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

    url_test("/foo//bar", "/foo_bar"),
    url_test("/foo//bar//baz", "/foo_bar_baz"),

    url_test("/samples/canvas-tutorial/2_1_canvas_rect.html" ,"/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Rectangular_shape_example"),
    url_test("/samples/canvas-tutorial/2_2_canvas_moveto.html" ,"/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Moving_the_pen"),
    url_test("/samples/canvas-tutorial/2_3_canvas_lineto.html" ,"/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Lines"),
    url_test("/samples/canvas-tutorial/2_4_canvas_arc.html" ,"/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Arcs"),
    url_test("/samples/canvas-tutorial/2_5_canvas_quadraticcurveto.html" ,"/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Quadratic_Bezier_curves"),
    url_test("/samples/canvas-tutorial/2_6_canvas_beziercurveto.html" ,"/docs/Web/API/Canvas_API/Tutorial/Drawing_shapes#Cubic_Bezier_curves"),
    url_test("/samples/canvas-tutorial/3_1_canvas_drawimage.html" ,"/docs/Web/API/Canvas_API/Tutorial/Using_images#Drawing_images"),
    url_test("/samples/canvas-tutorial/3_2_canvas_drawimage.html" ,"/docs/Web/API/Canvas_API/Tutorial/Using_images#Example.3A_Tiling_an_image"),
    url_test("/samples/canvas-tutorial/3_3_canvas_drawimage.html" ,"/docs/Web/API/Canvas_API/Tutorial/Using_images#Example.3A_Framing_an_image"),
    url_test("/samples/canvas-tutorial/3_4_canvas_gallery.html" ,"/docs/Web/API/Canvas_API/Tutorial/Using_images#Art_gallery_example"),
    url_test("/samples/canvas-tutorial/4_1_canvas_fillstyle.html" ,"/docs/Web/API/CanvasRenderingContext2D.fillStyle"),
    url_test("/samples/canvas-tutorial/4_2_canvas_strokestyle.html" ,"/docs/Web/API/CanvasRenderingContext2D.strokeStyle"),
    url_test("/samples/canvas-tutorial/4_3_canvas_globalalpha.html" ,"/docs/Web/API/CanvasRenderingContext2D.globalAlpha"),
    url_test("/samples/canvas-tutorial/4_4_canvas_rgba.html" ,"/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#An_example_using_rgba()"),
    url_test("/samples/canvas-tutorial/4_5_canvas_linewidth.html" ,"/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_lineWidth_example"),
    url_test("/samples/canvas-tutorial/4_6_canvas_linecap.html" ,"/docs/Web/API/CanvasRenderingContext2D.lineCap"),
    url_test("/samples/canvas-tutorial/4_7_canvas_linejoin.html" ,"/docs/Web/API/CanvasRenderingContext2D.lineJoin"),
    url_test("/samples/canvas-tutorial/4_8_canvas_miterlimit.html" ,"/docs/Web/API/CanvasRenderingContext2D.miterLimit"),
    url_test("/samples/canvas-tutorial/4_9_canvas_lineargradient.html" ,"/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_createLinearGradient_example"),
    url_test("/samples/canvas-tutorial/4_10_canvas_radialgradient.html" ,"/docs/Web/API/Canvas_API/Tutorial/Applying_styles_and_colors#A_createRadialGradient_example"),
    url_test("/samples/canvas-tutorial/4_11_canvas_createpattern.html" ,"/docs/Web/API/CanvasRenderingContext2D.createPattern"),
    url_test("/samples/canvas-tutorial/5_1_canvas_savestate.html" ,"/docs/Web/API/Canvas_API/Tutorial/Transformations#A_save_and_restore_canvas_state_example"),
    url_test("/samples/canvas-tutorial/5_2_canvas_translate.html" ,"/docs/Web/API/CanvasRenderingContext2D.translate"),
    url_test("/samples/canvas-tutorial/5_3_canvas_rotate.html" ,"/docs/Web/API/CanvasRenderingContext2D.rotate"),
    url_test("/samples/canvas-tutorial/5_4_canvas_scale.html" ,"/docs/Web/API/CanvasRenderingContext2D.scale"),
    url_test("/samples/canvas-tutorial/6_1_canvas_composite.html" ,"/docs/Web/API/CanvasRenderingContext2D.globalCompositeOperation"),
    url_test("/samples/canvas-tutorial/6_2_canvas_clipping.html" ,"/docs/Web/API/Canvas_API/Tutorial/Compositing#Clipping_paths"),
    url_test("/samples/canvas-tutorial/globalCompositeOperation.html" ,"/docs/Web/API/CanvasRenderingContext2D.globalCompositeOperation"),

    url_test("/samples/domref/mozGetAsFile.html", "/docs/Web/API/HTMLCanvasElement.mozGetAsFile"),

))

GITHUB_IO_URLS = flatten((
    # http://mdn.github.io
    # canvas raycaster
    url_test("/samples/raycaster/input.js", "http://mdn.github.io/canvas-raycaster/input.js"),
    url_test("/samples/raycaster/Level.js", "http://mdn.github.io/canvas-raycaster/Level.js"),
    url_test("/samples/raycaster/Player.js", "http://mdn.github.io/canvas-raycaster/Player.js"),
    url_test("/samples/raycaster/RayCaster.html", "http://mdn.github.io/canvas-raycaster/index.html"),
    url_test("/samples/raycaster/RayCaster.js", "http://mdn.github.io/canvas-raycaster/RayCaster.js"),
    url_test("/samples/raycaster/trace.css", "http://mdn.github.io/canvas-raycaster/trace.css"),
    url_test("/samples/raycaster/trace.js", "http://mdn.github.io/canvas-raycaster/trace.js"),

    # Bug 1215255 - Redirect static WebGL examples
    url_test("/samples/webgl/sample1", "http://mdn.github.io/webgl-examples/tutorial/sample1"),
    url_test("/samples/webgl/sample1/index.html", "http://mdn.github.io/webgl-examples/tutorial/sample1/index.html"),
    url_test("/samples/webgl/sample1/webgl-demo.js", "http://mdn.github.io/webgl-examples/tutorial/sample1/webgl-demo.js"),
    url_test("/samples/webgl/sample1/webgl.css", "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
    url_test("/samples/webgl/sample2", "http://mdn.github.io/webgl-examples/tutorial/sample2"),
    url_test("/samples/webgl/sample2/glUtils.js", "http://mdn.github.io/webgl-examples/tutorial/glUtils.js"),
    url_test("/samples/webgl/sample2/index.html", "http://mdn.github.io/webgl-examples/tutorial/sample2/index.html"),
    url_test("/samples/webgl/sample2/sylvester.js", "http://mdn.github.io/webgl-examples/tutorial/sylvester.js"),
    url_test("/samples/webgl/sample2/webgl-demo.js", "http://mdn.github.io/webgl-examples/tutorial/sample2/webgl-demo.js"),
    url_test("/samples/webgl/sample2/webgl.css", "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
    url_test("/samples/webgl/sample3", "http://mdn.github.io/webgl-examples/tutorial/sample3"),
    url_test("/samples/webgl/sample3/glUtils.js", "http://mdn.github.io/webgl-examples/tutorial/glUtils.js"),
    url_test("/samples/webgl/sample3/index.html", "http://mdn.github.io/webgl-examples/tutorial/sample3/index.html"),
    url_test("/samples/webgl/sample3/sylvester.js", "http://mdn.github.io/webgl-examples/tutorial/sylvester.js"),
    url_test("/samples/webgl/sample3/webgl-demo.js", "http://mdn.github.io/webgl-examples/tutorial/sample3/webgl-demo.js"),
    url_test("/samples/webgl/sample3/webgl.css", "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
    url_test("/samples/webgl/sample4", "http://mdn.github.io/webgl-examples/tutorial/sample4"),
    url_test("/samples/webgl/sample4/glUtils.js", "http://mdn.github.io/webgl-examples/tutorial/glUtils.js"),
    url_test("/samples/webgl/sample4/index.html", "http://mdn.github.io/webgl-examples/tutorial/sample4/index.html"),
    url_test("/samples/webgl/sample4/sylvester.js", "http://mdn.github.io/webgl-examples/tutorial/sylvester.js"),
    url_test("/samples/webgl/sample4/webgl-demo.js", "http://mdn.github.io/webgl-examples/tutorial/sample4/webgl-demo.js"),
    url_test("/samples/webgl/sample4/webgl.css", "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
    url_test("/samples/webgl/sample5", "http://mdn.github.io/webgl-examples/tutorial/sample5"),
    url_test("/samples/webgl/sample5/glUtils.js", "http://mdn.github.io/webgl-examples/tutorial/glUtils.js"),
    url_test("/samples/webgl/sample5/index.html", "http://mdn.github.io/webgl-examples/tutorial/sample5/index.html"),
    url_test("/samples/webgl/sample5/sylvester.js", "http://mdn.github.io/webgl-examples/tutorial/sylvester.js"),
    url_test("/samples/webgl/sample5/webgl-demo.js", "http://mdn.github.io/webgl-examples/tutorial/sample5/webgl-demo.js"),
    url_test("/samples/webgl/sample5/webgl.css", "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
    url_test("/samples/webgl/sample6", "http://mdn.github.io/webgl-examples/tutorial/sample6"),
    url_test("/samples/webgl/sample6/cubetexture.png", "http://mdn.github.io/webgl-examples/tutorial/sample6/cubetexture.png"),
    url_test("/samples/webgl/sample6/glUtils.js", "http://mdn.github.io/webgl-examples/tutorial/glUtils.js"),
    url_test("/samples/webgl/sample6/index.html", "http://mdn.github.io/webgl-examples/tutorial/sample6/index.html"),
    url_test("/samples/webgl/sample6/sylvester.js", "http://mdn.github.io/webgl-examples/tutorial/sylvester.js"),
    url_test("/samples/webgl/sample6/webgl-demo.js", "http://mdn.github.io/webgl-examples/tutorial/sample6/webgl-demo.js"),
    url_test("/samples/webgl/sample6/webgl.css", "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
    url_test("/samples/webgl/sample7", "http://mdn.github.io/webgl-examples/tutorial/sample7"),
    url_test("/samples/webgl/sample7/cubetexture.png", "http://mdn.github.io/webgl-examples/tutorial/sample7/cubetexture.png"),
    url_test("/samples/webgl/sample7/glUtils.js", "http://mdn.github.io/webgl-examples/tutorial/glUtils.js"),
    url_test("/samples/webgl/sample7/index.html", "http://mdn.github.io/webgl-examples/tutorial/sample7/index.html"),
    url_test("/samples/webgl/sample7/sylvester.js", "http://mdn.github.io/webgl-examples/tutorial/sylvester.js"),
    url_test("/samples/webgl/sample7/webgl-demo.js", "http://mdn.github.io/webgl-examples/tutorial/sample7/webgl-demo.js"),
    url_test("/samples/webgl/sample7/webgl.css", "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
    url_test("/samples/webgl/sample8", "http://mdn.github.io/webgl-examples/tutorial/sample8"),
    url_test("/samples/webgl/sample8/Firefox.ogv", "http://mdn.github.io/webgl-examples/tutorial/sample8/Firefox.ogv"),
    url_test("/samples/webgl/sample8/glUtils.js", "http://mdn.github.io/webgl-examples/tutorial/glUtils.js"),
    url_test("/samples/webgl/sample8/index.html", "http://mdn.github.io/webgl-examples/tutorial/sample8/index.html"),
    url_test("/samples/webgl/sample8/sylvester.js", "http://mdn.github.io/webgl-examples/tutorial/sylvester.js"),
    url_test("/samples/webgl/sample8/webgl-demo.js", "http://mdn.github.io/webgl-examples/tutorial/sample8/webgl-demo.js"),
    url_test("/samples/webgl/sample8/webgl.css", "http://mdn.github.io/webgl-examples/tutorial/webgl.css"),
))

MOZILLADEMOS_URLS = flatten((
    # https://mdn.mozillademos.org/
    url_test("/samples/canvas-tutorial/images/backdrop.png", "https://mdn.mozillademos.org/files/5395/backdrop.png"),
    url_test("/samples/canvas-tutorial/images/bg_gallery.png", "https://mdn.mozillademos.org/files/5415/bg_gallery.png"),
    url_test("/samples/canvas-tutorial/images/gallery_1.jpg", "https://mdn.mozillademos.org/files/5399/gallery_1.jpg"),
    url_test("/samples/canvas-tutorial/images/gallery_2.jpg", "https://mdn.mozillademos.org/files/5401/gallery_2.jpg"),
    url_test("/samples/canvas-tutorial/images/gallery_3.jpg", "https://mdn.mozillademos.org/files/5403/gallery_3.jpg"),
    url_test("/samples/canvas-tutorial/images/gallery_4.jpg", "https://mdn.mozillademos.org/files/5405/gallery_4.jpg"),
    url_test("/samples/canvas-tutorial/images/gallery_5.jpg", "https://mdn.mozillademos.org/files/5407/gallery_5.jpg"),
    url_test("/samples/canvas-tutorial/images/gallery_6.jpg", "https://mdn.mozillademos.org/files/5409/gallery_6.jpg"),
    url_test("/samples/canvas-tutorial/images/gallery_7.jpg", "https://mdn.mozillademos.org/files/5411/gallery_7.jpg"),
    url_test("/samples/canvas-tutorial/images/gallery_8.jpg", "https://mdn.mozillademos.org/files/5413/gallery_8.jpg"),
    url_test("/samples/canvas-tutorial/images/picture_frame.png", "https://mdn.mozillademos.org/files/242/Canvas_picture_frame.png"),
    url_test("/samples/canvas-tutorial/images/rhino.jpg", "https://mdn.mozillademos.org/files/5397/rhino.jpg"),
    url_test("/samples/canvas-tutorial/images/wallpaper.png", "https://mdn.mozillademos.org/files/222/Canvas_createpattern.png"),
))

