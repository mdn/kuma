
(function($) {
    'use strict';

    var faqContainer = $('#contributions-page');
    var thumbsUp = faqContainer.find('.thumbs-up');
    var thumbsDown = faqContainer.find('.thumbs-down');
    var faqFeedback = faqContainer.find('#faq-feedback');

    function sendAnalyticsVoteEvent(action, label ,value) {
        var event = {
            category: 'payments',
            action: action,
            value: value,
        };

        if (label) {
            event.label = label;
        }

        mdn.analytics.trackEvent(event);
    }

    function onThumbsUp(event) {
        var questionNumber = $(event.target).attr('data-faq') || 0;

        $(event.target).next().removeClass('active');
        $(event.target).addClass('active');

        sendAnalyticsVoteEvent('FAQ vote', 'question_' + questionNumber, 1);
    }

    function onThumbsDown(event) {
        var questionNumber = $(event.target).attr('data-faq') || 0;

        $(event.target).prev().removeClass('active');
        $(event.target).addClass('active');

        sendAnalyticsVoteEvent('FAQ vote', 'question_' + questionNumber, 0);
    }


    function onFeedback(event) {
        event.preventDefault();

        var feedback = $(this).find('textarea').val();
        if (feedback) {
            mdn.analytics.trackEvent({
                category: 'payments',
                action: 'FAQ - Any other questions',
                label: feedback,
            });
        }
    }

    thumbsUp.click(onThumbsUp);
    thumbsDown.click(onThumbsDown);
    faqFeedback.submit(onFeedback);
})(jQuery);
