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
            new SB(gettext('Bold'), '/media/img/markup/text_bold.png',
                   "'''", "'''", gettext('bold text')),
            new SB(gettext('Italic'), '/media/img/markup/text_italic.png',
                   "''", "''", gettext('italic text')),
            new Marky.Separator(),
            new SB(gettext('Article Link'), '/media/img/markup/page_link.png',
                   '[[', ']]', gettext('Knowledge Base Article')),
            new SB(gettext('External Link'),
                   '/media/img/markup/world_link.png', '[http://example.com ',
                   ']', gettext('external link')),
            new Marky.Separator(),
            new SB(gettext('Numbered List'),
                   '/media/img/markup/text_list_numbers.png', '# ', '',
                   gettext('Numbered list item'), true),
            new SB(gettext('Bulleted List'),
                   '/media/img/markup/text_list_bullets.png', '* ', '',
                   gettext('Bulleted list item'), true),
            new Marky.Separator(),
            new SB(gettext('Heading 1'), '/media/img/markup/h1.png', '=',
                   '=', gettext('Heading 1')),
            new SB(gettext('Heading 2'), '/media/img/markup/h2.png', '==',
                   '==', gettext('Heading 2')),
            new SB(gettext('Heading 3'), '/media/img/markup/h3.png', '===',
                   '===', gettext('Heading 3'))
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
    // Gets the DOM node for the button.
    node: function() {
        var me = this,
            $btn = $(this.html);
        $btn.attr({
            src: this.imagePath,
            title: this.name,
            alt: this.name
        }).click(function(e) {
            me.handleClick();
        });
        return $btn[0];
    },
    // Handles the button click.
    handleClick: function() {
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
    },
    _applyEveryLine: function(opentag, closetag, block) {
        return $.map(block.split('\n'), function(line) {
            return (line.replace(/\s+/, '').length ?
                    opentag + line + closetag : line);
        });
    }
};

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
