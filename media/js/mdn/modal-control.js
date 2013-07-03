/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

$(document).ready(function() {

    // When a modal link is clicked
    $(".modal").click(function () {
            
        var width  = 600,
            height = 400,
            href   = $(this).attr("href");

        href += ((href.indexOf("?") == -1) ? "?" : "&") + "popup=1";

        // Open the modal to the iframe address provided by the link
        $.modal(
            "<iframe style='border:0' scrolling='no' src='" + href + "' height='" + height + "' width='" + width + "'>", 
            {
                overlayClose: true,
                containerCss: { width: width, height: height },
                dataCss: { overflow: "hidden" },
                onOpen: function (dialog) {
                    dialog.wrap.css({ overflow: "hidden" });
                    dialog.overlay.show();
                    dialog.container.show();
                    dialog.data.show();
                }
            }
        );

        return false;
    });

    // Close the modal when the "x" is clicked
    $(".closeModal").click(function () {
        if (top.$ && top.$.modal) {
            top.$.modal.close();
        }
        return false;
    });
});