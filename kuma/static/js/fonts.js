(function(win, doc, $) {
    /*
        Font Loading
    */

    // what fonts are we loading?
    var fonts = [
        {
            'name' : 'Open Sans Light',
            'class' : 'ffo-opensanslight',
            'varient' : [
                {'weight' : 'normal'},
                {'weight' : 'bold'},
                {'style' : 'italic'}
            ]
        },
        {
            'name' : 'Open Sans',
            'class' : 'ffo-opensans',
            'varient' : [
                {'weight' : 'normal'},
                {'weight' : 'bold'},
                {'style' : 'italic'}
            ]
        }
    ];

    // to collect the results of the observers as they return
    var fontsLoaded = {};

    // timout for all observers
    var ffoTimeout = 2000;

    // run the observer plug in
    ffoLoad();

    // starts observers for all fonts in fonts array
    function ffoLoad() {
        // for each font
        $.each(fonts, function() {
            // add the class to the fontsLoaded object
            var fontClass = this.class;

            // get name for later use
            var fontName = this.name;

            fontsLoaded[fontClass] = {};

            // for each varient of this font
            $.each(this.varient, function(index) {
                var fontVarient = this;
                var fontVarientNumber = index;

                // add observer for this varient
                var ffObserver = new FontFaceObserver(fontName, fontVarient);

                // add an object to the fontsLoaded object
                fontsLoaded[fontClass][fontVarientNumber] = false;

                // add callbacks for this observer
                ffObserver.check(null, ffoTimeout).then(function () {
                    // update fontsLoaded object to show it loaded
                    fontsLoaded[fontClass][fontVarientNumber] = true;
                    ffoCheck();
                }, function () {
                    // timeout
                    ffoCheck();
                });

            });
        });
    }

    function ffoCheck(){
        var allLoaded = true;

        // loop through fontsLoaded looking to see if they've loaded
        $.each(fontsLoaded, function(){
            var isLoaded = true;
            $.each(this, function(){
                if(this == false) {
                    isLoaded = false;
                }
            })
            if(isLoaded == false) {
                allLoaded = false;
            }
        });

        // if all fonts are loaded swap font in
        if(allLoaded) {
            ffoFinished();

            // set cookie so fonts are displayed automatically with the server's help
            var expires = new Date();
            expires.setDate(expires.getDate() + 1);
            document.cookie = 'ffo=true; expires=' + expires + '; path=/';
        }
    }

    function ffoFinished() {
        ffoSwap();
    }

    function ffoSwap() {
        // swaps in available fonts
        $.each(fontsLoaded, function(index) {
            var fontAttribute = index;
            var fontLoaded = true;

            $.each(this, function() {
                if(this == false) {
                    fontLoaded = false;
                }
            })
            if(fontLoaded == true) {
                $('html').attr('data-' + fontAttribute, true);
            }
        });
    }

})(window, document, jQuery);
