(function($, mdn) {
    'use strict';

    var $survey;
    var $votes;
    var gaChecks = 0;

    // ga loads async, so there's a chance it wont be available when this
    // script is parsed. we'll give it 2 seconds.
    function checkGA() {
        // survey won't do much good if we can't store the data
        // checking for ".create" due to Ghostery mocking of ga
        if (window.ga && ga.create) {
            showSurvey();
        } else if (gaChecks < 5) {
            setTimeout(checkGA, 500);
            gaChecks++;
        }
    }

    function showSurvey() {
        $survey = $('#helpful-survey');
        $votes = $survey.find('.helpful-survey-vote');

        $survey.removeClass('hidden');

        $votes.on('click', function() {
            // store the vote in ye olde google
            mdn.analytics.trackEvent({
                category: 'helpful2',
                action: 'vote',
                label: $(this).hasClass('helpful-survey-yes') ? 'Yes' : 'No'
            });

            // disable the buttons for browsers that don't get pointer-events
            $votes.prop('disabled', 'disabled');

            // hide buttons and display thank you message
            $survey.addClass('submitted');
        });
    }

    checkGA();
})(window.jQuery, window.mdn);
