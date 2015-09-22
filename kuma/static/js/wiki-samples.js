(function(win, doc, $) {
    "use strict";

    if(!win.waffle || !win.waffle.flag_is_active('wiki_samples')) return;

    var sites = ['codepen', 'jsfiddle'];
    var frameLength = 'frame_'.length;

    var sourceURL = $('link[rel=canonical]').attr('href') || win.location.href.split('#')[0];
    var plug = '<!-- Learn about this code on MDN: ' + sourceURL + ' -->\n\n';

    var analytics = '<input type="hidden" name="utm_source" value="mdn" />' +
                    '<input type="hidden" name="utm_medium" value="code-sample" />' +
                    '<input type="hidden" name="utm_campaign" value="external-samples" />';

    // Find sample IFRAMES
    // Some are wrapped in tables, so put the button after the table or after the iframe
    $('.sample-code-frame').each(function() {
        var $this = $(this);
        var parentTable = $this.parents('.sample-code-table').get(0);
        var section = $this.attr('id').substring(frameLength);
        var source = $this.attr('src').replace(/^https?:\/\//,'');
        source = source.slice(source.indexOf('/'), source.indexOf('$'));

        $(parentTable || $this).after(function() {
            return createSampleButtons(section, source);
        });
    });

    // Listen for clicks on open buttons
    $('#wikiArticle').on('click', 'button.open-in-host', function(){
        var $button = $(this);
        var section = $button.attr('data-section');
        var source  = $button.attr('data-source');
        var sampleCodeHost = $button.attr('data-host');

        // track the click and sample code host
        mdn.analytics.trackEvent({
            category: 'Samples',
            action: 'open-' + sampleCodeHost,
            label: section
        });

        // disable the button, till we open the fiddle
        $button.attr('disabled', 'disabled');
        $.get(source + '?section=' + section + '&raw=1').then(function(sample) {
            var $sample = $('<div />').append(sample);
            var htmlCode = $sample.find('pre[class*=html]').text();
            var cssCode = $sample.find('pre[class*=css]').text();
            var jsCode = $sample.find('pre[class*=js]').text();
            var title = $sample.find('h2[name=' + section + ']').text();

            openSample(sampleCodeHost, title, htmlCode, cssCode, jsCode);

            $button.removeAttr('disabled');
        });
    });

    function openJSFiddle(title, htmlCode, cssCode, jsCode) {
       var $form = $('<form method="post" action="https://jsfiddle.net/api/mdn/" class="hidden">' +
            '<input type="hidden" name="html" />' +
            '<input type="hidden" name="css" />' +
            '<input type="hidden" name="js" />' +
            '<input type="hidden" name="title" />' +
            '<input type="hidden" name="wrap" value="b" />' + analytics +
            '<input type="submit" />' +
        '</form>').appendTo(doc.body);

       $form.find('input[name=html]').val(plug + htmlCode);
       $form.find('input[name=css]').val(cssCode);
       $form.find('input[name=js]').val(jsCode);
       $form.find('input[name=title]').val(title);
       $form.get(0).submit();
    }

    function openCodepen(title, htmlCode, cssCode, jsCode) {
       var $form = $('<form method="post" action="https://codepen.io/pen/define" class="hidden">' +
            '<input type="hidden" name="data">' + analytics +
            '<input type="submit" />' +
        '</form>').appendTo(doc.body);

       var data = {'title': title, 'html': plug + htmlCode, 'css': cssCode, 'js': jsCode};
       $form.find('input[name=data]').val(JSON.stringify(data));
       $form.get(0).submit();
    }

    function openSample(sampleCodeHost, title, htmlCode, cssCode, jsCode) {
       if(sampleCodeHost === 'jsfiddle') {
            openJSFiddle(title, htmlCode, cssCode, jsCode);
        } else if(sampleCodeHost === 'codepen') {
            openCodepen(title, htmlCode, cssCode, jsCode);
        }
    }

    function createSampleButtons(section, source) {
        var $parent = $('<div class="open-in-host-container" />');

        $.each(sites, function(){
            // convert sitename to lowercase for icon name and host identifier
            var host = this.toLowerCase();
            $parent.append([
                '<button class="open-in-host" ',
                        'data-host="', host, '" ',
                        'data-section="', section, '"',
                        'data-source="', source, '">',
                    '<i aria-hidden="true" class="icon-', host,'"></i> ',
                    'Open in ', this,
                '</button>'
            ].join(''));
        });

        return $parent;
    }

})(window, document, jQuery);
