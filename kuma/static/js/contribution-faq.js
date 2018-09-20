
(function($) {
    'use strict';

    var faqContainer = $('#contributions-page');
    var thumbsUp = faqContainer.find('.thumbs-up');
    var thumbsDown = faqContainer.find('.thumbs-down');
    var faqFeedback = faqContainer.find('#faq-feedback');

    function sendAnalyticsVoteEvent(action, label ,value) {
        var event = {
            category: 'FAQ Feedback',
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

        sendAnalyticsVoteEvent('question_' + questionNumber, null, 1);
    }

    function onThumbsDown(event) {
        var questionNumber = $(event.target).attr('data-faq') || 0;

        $(event.target).prev().removeClass('active');
        $(event.target).addClass('active');

        sendAnalyticsVoteEvent('question_' + questionNumber, null, 0);
    }


    function onFeedback(event) {
        event.preventDefault();

        var feedback = $(this).find('textarea').val() || '';
        var action = $(this).find('textarea').attr('data-action') || '';
        mdn.analytics.trackEvent({
            category: 'Contribution feedback',
            action: action,
            label: feedback,
        });
    }

    thumbsUp.click(onThumbsUp);
    thumbsDown.click(onThumbsDown);
    faqFeedback.submit(onFeedback);
})(jQuery);
