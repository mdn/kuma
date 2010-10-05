/*global Marky, document, jQuery */
/*
 * forums.js
 * Scripts for the forums app.
 */

(function($){

    function init() {
        Marky.createSimpleToolbar('.forum-editor-tools', '#reply-content, #id_content');
    }

    $(document).ready(init);

}(jQuery));
