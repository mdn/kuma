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

        var $sampleFrame = parentTable ? parentTable : $this;
        createSampleButtons($sampleFrame, section, source);
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

    function openSample(sampleCodeHost, section, title, htmlCode, cssCode, jsCode) {
        // replace &nbsp; in CSS Samples to fix bug 1284781
        var cssCleanCode = cssCode.replace(/\xA0/g, " ");
        //track the click and sample code host as event
        mdn.analytics.trackEvent({
            category: 'Samples',
            action: 'open-' + sampleCodeHost,
            label: section
        });
        // add user to segement that has used samples
        if(win.ga) ga('set', 'dimension8', 'Yes');

        if(sampleCodeHost === 'jsfiddle') {
            openJSFiddle(title, htmlCode, cssCleanCode, jsCode);
        } else if(sampleCodeHost === 'codepen') {
            openCodepen(title, htmlCode, cssCleanCode, jsCode);
        }
    }

    function createSampleButtons($sampleFrame, section, source) {
        // get this sample's html/css/js
        $.get(source + '?section=' + section + '&raw=1').then(function(sample) {
            var $sample = $('<div />').append(sample);
            var htmlCode = $sample.find('pre[class*=html]').text();
            var cssCode = $sample.find('pre[class*=css]').text();
            var jsCode = $sample.find('pre[class*=js]').text();
            // jquery can't handled all our IDs, need to use vanailla js for this
            // http://stackoverflow.com/questions/7695898/uncaught-exception-syntax-error-unrecognized-expression-jquery
            var title = doc.getElementById(section);
            title = title ? title.textContent : '';
            // check that there is enough data to add buttons
            if(htmlCode.length || cssCode.length || jsCode.length){
                // add buttons if we have good data
                var $buttonContainer = $('<div class="open-in-host-container" />');
                $.each(sites, function() {
                    // convert sitename to lowercase for icon name and host identifier
                    var sampleCodeHost = this.toLowerCase();
                    // create button
                    var $button = $('<button />', { 'class': 'open-in-host' });
                    // create icon
                    var $icon = $('<i />', { 'class': 'icon-' + sampleCodeHost, 'aria-hidden': 'true' });
                    // create text
                    var $text = interpolate(gettext('Open in %(site)s'), {site: this}, true) + ' ';

                    // add button icon and text to DOM
                    $button.append($text).append($icon).appendTo($buttonContainer);
                    $buttonContainer.insertAfter($sampleFrame);

                    // add listener for button interactions
                    $button.on('click', function(){
                        openSample(sampleCodeHost, section, title, htmlCode, cssCode, jsCode);
                    });
                });
            } else if($sample.children().length == 0) {
                // no content, log error
                mdn.analytics.trackError('embedLiveSample Error', '$sample was empty', section);
            } else {
                // no content, log error
                mdn.analytics.trackError('embedLiveSample Error', '$sample did not cointain any code', section);
            }
        }).fail( function() {
            mdn.analytics.trackError('embedLiveSample Error', 'ajax error retreiving source', section);
        });
    }

})(window, document, jQuery);
