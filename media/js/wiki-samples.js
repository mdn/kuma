(function(win, doc, $) {

    var sites = ['jsfiddle', 'codepen'];

    // using id to get sample code section since macros discard other attributes
    $('.sample-code-frame').before(function() {
        var section = $(this).attr('id').substring("frame_".length);
        return createSampleButtons(section, sites);
    });
    $('.sample-code-table').before(function(){
        var section = $(this).find('iframe').attr('id').substring("frame_".length);
        return createSampleButtons(section, sites);
    });

    $('#wikiArticle').on('click', 'button.open-in-host', function(){
        var $button = $(this);
        var section = $button.attr('data-section');
        var sampleCodeHost = $button.attr('data-host');
        var sampleUrl = win.location.href.split('#')[0] + '?section=' + section + '&raw=1';

        // track the click and sample code host
        mdn.analytics.trackEvent({
            category: 'Samples',
            action: 'open-' + sampleCodeHost,
            label: section
        });

        // disable the button, till we open the fiddle
        $button.attr('disabled', 'disabled');
        $.get(sampleUrl).then(function(sample) {
            var $sample = $('<div />').append(sample);
            var htmlCode = $sample.find('.brush\\:.html, .brush\\:.html\\;').text();
            var cssCode = $sample.find('.brush\\:.css, .brush\\:.css\\;').text();
            var jsCode = $sample.find('.brush\\:.js, .brush\\:.js\\;').text();
            var title = $sample.find('h2[name=' + section + ']').text();
            openSample(sampleCodeHost, title, htmlCode, cssCode, jsCode);

            $button.removeAttr('disabled');
        });
    });

    function openJSFiddle(title, htmlCode, cssCode, jsCode) {
       var $form = $('<form method="post" target="_blank" action="https://jsfiddle.net/api/mdn/" class="hidden">'
            + '<input type="hidden" name="html" />'
            + '<input type="hidden" name="css" />'
            + '<input type="hidden" name="js" />'
            + '<input type="hidden" name="title" />'
            + '<input type="hidden" name="wrap" value="b" />'
            + '<input type="submit" />'
        + '</form>').appendTo(doc.body);
       $form.find('input[name=html]').val(htmlCode);
       $form.find('input[name=css]').val(cssCode);
       $form.find('input[name=js]').val(jsCode);
       $form.find('input[name=title]').val(title);
       $form.get(0).submit();
    }

    function openCodepen(title, htmlCode, cssCode, jsCode) {
       var $form = $('<form method="post" target="_blank" action="http://codepen.io/pen/define" class="hidden">'
            + '<input type="hidden" name="data">'
            + '<input type="submit" />'
        + '</form>').appendTo(doc.body);
       var data = {'title': title, 'html': htmlCode, 'css': cssCode, 'js': jsCode};
       $form.find('input[name=data]').val(JSON.stringify(data));
       $form.get(0).submit();
    }

    function openSample(sampleCodeHost, title, htmlCode, cssCode, jsCode) {
       if(sampleCodeHost == 'jsfiddle') {
            openJSFiddle(title, htmlCode, cssCode, jsCode);
        } else if(sampleCodeHost == 'codepen') {
            openCodepen(title, htmlCode, cssCode, jsCode);
        }
    }

    function createSampleButtons(section, sites) {
        var buttons = '<div style="margin-bottom:10px;">';
        sites.forEach(function(site){
            // convert sitename to lowercase for icon name and host identifier
            buttons += '<button class="open-in-host" data-host="'+ site.toLowerCase() +'" data-section="' +
                section + '"><i aria-hidden="true" class="icon-'+ site.toLowerCase() +'"></i> Open in ' +
                site +'</button>';
        });
        buttons += '</div>';
        return buttons;
    }

})(window, document, jQuery)
