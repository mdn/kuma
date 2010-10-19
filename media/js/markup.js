/*global window, document, jQuery, gettext */
/*
    Marky, the markup toolbar builder

    Usage:
    <script type="text/javascript">
        // Create the simple toolbar (used in Forums and Questions)
        Marky.createSimpleToolbar('#toolbar-container-id', '#textarea-id');

        // or, create the full toolbar (used in the Knowledgebase)
        Marky.createFullToolbar('#toolbar-container-id', '#textarea-id');

        //or, create a custom toolbar.
        Marky.createFullToolbar('#toolbar-container-id', '#textarea-id', [
            new Marky.SimpleButton(
                gettext('Bold'), '/media/img/markup/text_bold.png', "'''",
                "'''", gettext('bold text')),
            new Marky.SimpleButton(
                gettext('Italic'), '/media/img/markup/text_italic.png', "''",
                "''", gettext('italic text'))
        ]);
    </script>

*/
(function($, gettext, document){

var Marky = {
    createSimpleToolbar: function(toolbarSel, textareaSel) {
        var SB = Marky.SimpleButton;
        var buttons = [
            new SB(gettext('Bold'), '/media/img/markup/text_bold.png',
                   "'''", "'''", gettext('bold text')),
            new SB(gettext('Italic'), '/media/img/markup/text_italic.png',
                   "''", "''", gettext('italic text')),
            new SB(gettext('Article Link'), '/media/img/markup/page_link.png',
                   '[[', ']]', gettext('Knowledge Base Article')),
            new SB(gettext('External Link'),
                   '/media/img/markup/world_link.png', '[http://example.com ',
                   ']', gettext('external link')),
            new SB(gettext('Numbered List'),
                   '/media/img/markup/text_list_numbers.png', '# ', '',
                   gettext('Numbered list item'), true),
            new SB(gettext('Bulleted List'),
                   '/media/img/markup/text_list_bullets.png', '* ', '',
                   gettext('Bulleted list item'), true)
        ];
        Marky.createCustomToolbar(toolbarSel, textareaSel, buttons);
    },
    createFullToolbar: function(toolbarSel, textareaSel) {
        var SB = Marky.SimpleButton;
        var buttons = [
            new SB(gettext('Bold'), '/media/img/markup/new/bold.png',
                   "'''", "'''", gettext('bold text')),
            new SB(gettext('Italic'), '/media/img/markup/new/italic.png',
                   "''", "''", gettext('italic text')),
            new Marky.Separator(),
            // TODO: There will be only one link button that opens a helper
            new SB(gettext('Article Link'), '/media/img/markup/new/link.png',
                   '[[', ']]', gettext('Knowledge Base Article')),
            new SB(gettext('External Link'),
                   '/media/img/markup/new/link.png', '[http://example.com ',
                   ']', gettext('external link')),
            // TODO: implement media helper
            new SB(gettext('Insert Media'),
                  '/media/img/markup/new/image.png', '',
                  '', gettext('media')),
            new Marky.Separator(),
            new SB(gettext('Numbered List'),
                   '/media/img/markup/new/ol.png', '# ', '',
                   gettext('Numbered list item'), true),
            new SB(gettext('Bulleted List'),
                   '/media/img/markup/new/ul.png', '* ', '',
                   gettext('Bulleted list item'), true),
            new Marky.Separator(),
            new SB(gettext('Heading 1'), '/media/img/markup/new/h1.png', '=',
                   '=', gettext('Heading 1')),
            new SB(gettext('Heading 2'), '/media/img/markup/new/h2.png', '==',
                   '==', gettext('Heading 2')),
            new SB(gettext('Heading 3'), '/media/img/markup/new/h3.png', '===',
                   '===', gettext('Heading 3')),
            new Marky.Separator(),
            new Marky.ShowForButton()
        ];
        Marky.createCustomToolbar(toolbarSel, textareaSel, buttons);
    },
    createCustomToolbar: function(toolbarSel, textareaSel, partsArray) {
        var $toolbar = $(toolbarSel || '.forum-editor-tools'),
            textarea = $(textareaSel || '#reply-content, #id_content')[0];
        for (var i=0, l=partsArray.length; i<l; i++) {
            $toolbar.append(partsArray[i].bind(textarea).node());
        }
    }
};


/*
 * A simple button.
 * Note: `everyline` is a boolean value that says whether or not the selected
 *       text should be broken into multiple lines and have the markup applied
 *       to each line or not. Default is false (do not apply this behavior).
 */
Marky.SimpleButton = function(name, imagePath, openTag, closeTag, defaultText,
                              everyline) {
    this.name = name;
    this.imagePath = imagePath;
    this.openTag = openTag;
    this.closeTag = closeTag;
    this.defaultText = defaultText;
    this.everyline = everyline;

    this.html = '<img class="markup-toolbar-button" />';
};

Marky.SimpleButton.prototype = {
    // Binds the button to a textarea (DOM node).
    bind: function(textarea) {
        this.textarea = textarea;
        return this;
    },
    // Renders the html.
    render: function() {
        return $(this.html).attr({
            src: this.imagePath,
            title: this.name,
            alt: this.name
        });
    },
    // Gets the DOM node for the button.
    node: function() {
        var me = this,
            $btn = this.render();
        $btn.click(function(e) {
            me.handleClick(e);
        });
        return $btn[0];
    },
    // Handles the button click.
    handleClick: function(e) {
        var selText, selStart, selEnd, splitText, range,
            textarea = this.textarea;
        textarea.focus();

        if(document.selection && document.selection.createRange) {
            // IE/Opera
            range = document.selection.createRange();
            selText = range.text;
            if(!selText.length) {
                selText = this.defaultText;
            }

            if(this.everyline && -~selText.indexOf('\n')) {
                splitText = this._applyEveryLine(this.openTag, this.closeTag,
                                                 selText);
                range.text = splitText.join('\n');
            } else {
                range.text = this.openTag + selText + this.closeTag;

                if(range.moveStart) {
                    range.moveStart('character', (-1 * this.openTag.length) -
                                                 selText.length);
                    range.moveEnd('character', (-1 * this.closeTag.length));
                }
            }

            range.select();
        } else if(textarea.selectionStart || textarea.selectionStart == '0') {
            // Firefox/Safari/Chrome/etc.
            selStart = textarea.selectionStart;
            selEnd = textarea.selectionEnd;
            selText = textarea.value.substring(selStart, selEnd);
            if(!selText.length) {
                selText = this.defaultText;
            }

            if(this.everyline && -~selText.indexOf('\n')) {
                splitText = this._applyEveryLine(this.openTag, this.closeTag,
                                                 selText).join('\n');
                textarea.value =
                    textarea.value.substring(0, textarea.selectionStart) +
                    splitText +
                    textarea.value.substring(textarea.selectionEnd);

                textarea.selectionStart = selStart;
                textarea.selectionEnd = textarea.selectionStart +
                                        splitText.length;
            } else {
                textarea.value =
                    textarea.value.substring(0, textarea.selectionStart) +
                    this.openTag + selText + this.closeTag +
                    textarea.value.substring(textarea.selectionEnd);

                textarea.selectionStart = selStart + this.openTag.length;
                textarea.selectionEnd = textarea.selectionStart +
                                        selText.length;
            }
        }
        e.preventDefault();
        return false;
    },
    _applyEveryLine: function(opentag, closetag, block) {
        return $.map(block.split('\n'), function(line) {
            return (line.replace(/\s+/, '').length ?
                    opentag + line + closetag : line);
        });
    }
};

/*
 * The showfor helper link.
 */
Marky.ShowForButton = function() {
    this.name = gettext('Show for...');
    this.openTag = '{for}';
    this.closeTag = '{/for}';
    this.defaultText = 'Show for text.';
    this.everyline = false;

    this.html = '<a class="markup-toolbar-link" href="#show-for">Show For...</a>';
};

Marky.ShowForButton.prototype = $.extend({}, Marky.SimpleButton.prototype, {
    // Renders the html.
    render: function() {
        return $(this.html);
    },
    // Gets the DOM node for the button.
    node: function() {
        var me = this,
            $btn = this.render();
        $btn.click(function(e) {
            me.openModal(e);
        });
        return $btn[0];
    },
    openModal: function(e) {
        var me = this,
            // TODO: look at using a js template solution (jquery-tmpl?)
            $modal = $('<section id="showfor-modal" class="pop-in">' +
                       '<a href="#close" class="close">&#x2716;</a><h1/>' +
                       '<div class="wrap"><div class="placeholder"/>' +
                       '<div class="submit"><button type="button"></button>' +
                       '<a href="#cancel" class="cancel"></a></div>' +
                       '</div></section>'),
            $overlay = $('<div id="modal-overlay"></div>'),
            $placeholder = $modal.find('div.placeholder'),
            data = $.parseJSON($(this.textarea).attr('data-showfor'));

        $modal.find('h1').text(this.name);
        $modal.find('button').text(gettext('Add Rule')).click(function(e){
            var showfor = ''
            $('#showfor-modal input:checked').each(function(){
                showfor += ($(this).val() + ',');
            });
            me.openTag = '{for ' + showfor.slice(0,showfor.length-1) + '}';
            me.handleClick(e);
            closeModal(e);
        });
        $modal.find('a.cancel').text(gettext('Cancel'));
        appendOptions($placeholder, data.versions);
        appendOptions($placeholder, data.oses);
        $modal.find('a.close, a.cancel').click(closeModal);

        $('body').append($overlay).append($modal);

        function appendOptions($ph, options) {
            $.each(options, function(i, value) {
                $ph.append($('<h2/>').text(value[0]));
                $.each(value[1], function(i, value) {
                    $ph.append(
                        $('<label/>').text(value[1]).prepend(
                            $('<input type="checkbox" name="showfor"/>')
                                .attr('value', value[0])
                        )
                    );
                });
            });
        }

        function closeModal(e) {
            $modal.unbind().remove();
            $overlay.unbind().remove();
            delete $modal;
            delete $overlay;
            e.preventDefault();
            return false;
        }

        e.preventDefault();
        return false;
    }
});

/*
 * A button separator.
 */
Marky.Separator = function() {
    this.html = '<span class="separator"></span>';
};

Marky.Separator.prototype = {
    node: function() {
        return $(this.html)[0];
    },
    bind: function() {
        return this;
    }
};

window.Marky = Marky;

}(jQuery, gettext, document));
