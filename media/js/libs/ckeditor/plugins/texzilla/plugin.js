// CKEditor TeXZilla Plugin
// Copyright (C) 2014  Raniere Silva
//
// This Source Code Form is subject to the terms of the
// Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
// with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

/* global CKEDITOR: false */

CKEDITOR.plugins.add("texzilla", {
    icons: "texzilla",

    init: function(editor) {
        CKEDITOR.dialog.add("texzillaDialog",
            this.path + "dialogs/texzilla.js");

        editor.addCommand("texzillaDialog",
            new CKEDITOR.dialogCommand("texzillaDialog"));
        editor.ui.addButton("texzilla", {
            label: "Insert MathML based on (La)TeX",
            command: "texzillaDialog",
            icon: this.path + "icons/texzilla.png",
            toolbar: "insert"
        });
    }
});
