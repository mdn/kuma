(function ($) {
    function init() {
        initReadoutModes();
    }

    // Hook up readout mode links (like "This Week" and "All Time") to swap
    // table data.
    function initReadoutModes() {
        $(".readout-modes").each(
            function attachClickHandler() {
                var $modes = $(this),
                    slug = $modes.attr("data-slug");
                $modes.find(".mode").each(
                    function() {
                        var $button = $(this);
                        $button.click(
                            function switchMode() {
                                // Dim table to convey that its data isn't what
                                // the select mode indicates:
                                var $table = $("#" + slug + "-table");
                                $table.addClass("busy");

                                // Update button appearance:
                                $modes.find(".mode").removeClass("active");
                                $button.addClass("active");
                                $.get($button.attr("data-url"),
                                    function succeed(html) {
                                        $table.html(html).removeClass("busy");
                                    });
                                return false;
                            });
                    });
            });
    }

    $(document).ready(init);
}(jQuery));
