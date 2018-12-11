
(function($) {
    'use strict';

    var faqContainer = $('#contributions-page');
    var thumbsUp = faqContainer.find('.thumbs-up');
    var thumbsDown = faqContainer.find('.thumbs-down');
    var faqFeedback = faqContainer.find('#faq-feedback');
    var faqFeedbackConfirmation = faqContainer.find('.feedback-confirmation');

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

        var feedback = document.getElementById('contribution-feedback').value;
        if (feedback && feedback.trim !== '') {
            mdn.analytics.trackEvent({
                category: 'payments',
                action: 'FAQ - Any other questions',
                label: feedback,
            }, function() {
                faqFeedbackConfirmation.get(0).classList.remove('hidden');
                faqFeedbackConfirmation.get(0).removeAttribute('aria-hidden');
                faqFeedback.get(0).classList.add('disabled');
            });
        } else {
            faqFeedback.get(0).classList.remove('disabled');
        }
    }

    thumbsUp.click(onThumbsUp);
    thumbsDown.click(onThumbsDown);
    faqFeedback.submit(onFeedback);
})(jQuery);
