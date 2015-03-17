(function(win, doc, $) {

    $('.share-link').on('click', function(e) {
        e.preventDefault();

        var $this = $(this);
        var title = encodeURIComponent($this.data('title') || doc.title);
        var url = encodeURIComponent($this.data('url') || win.location);
        var track = function(site) {
            mdn.analytics.trackEvent({
                category: 'Social Share',
                action: site,
                label: url
            });
        };

        if($this.hasClass('twitter')) {
            open('http://twitter.com/share?url=' + url + '&text=' + title, 'twitter-share', 'height=400,width=550,resizable=1,toolbar=0,menubar=0,status=0,location=0');
            track('Twitter');
        }
        else if($this.hasClass('facebook')) {
            open('http://facebook.com/sharer.php?s=100&p[url]=' + url + '&p[images][0]=/media/redesign/img/favicon144.png&p[title]=' + title, 'facebook-share', 'height=380,width=660,resizable=0,toolbar=0,menubar=0,status=0,location=0,scrollbars=0');
            track('Facebook');
        }
        else if($this.hasClass('gplus')) {
            open('https://plus.google.com/share?url=' + url, 'gshare', 'height=270,width=630,resizable=0,toolbar=0,menubar=0,status=0,location=0,scrollbars=0');
            track('Google Plus');
        }

    });

})(window, document, jQuery);
