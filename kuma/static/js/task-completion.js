(function(win, doc, $) {

    // this feature requires localStorage
    if (win.mdn.features.localStorage) {
        // true if ever clicked ignore on helpfulness widget
        var ignore = localStorage.getItem('helpful-ignore') === 'true';
        // asked helpfulness recently?
        var helpfulnessAskedRecently = parseInt(localStorage.getItem('helpfulnessTracker'), 10) > Date.now();
        // asked task completion survey recently?
        var taskAskedRecently = parseInt(localStorage.getItem('taskTracker'), 10) > Date.now();

        if (!ignore && !taskAskedRecently && !helpfulnessAskedRecently) {
            inquire();
        }
    }

    function inquire() {

        // dimension14 is "Saw Survey Gizmo Task Completion survey"
        if(win.ga) ga('set', 'dimension14', 'Yes');
        ga('send', 'event', 'survey', 'prompt', 'impression', {
            nonInteraction: true
        });

        // construct question
        var path = encodeURIComponent(window.location.pathname);
        var clickTime = Date.now() + (1000*60)*20; // 20 min from now
        var surveyURL= 'https://www.surveygizmo.com/s3/2980494/do-or-do-not';
        var surveyLink = surveyURL + '?' + '&t='+ clickTime + '&p=' + path;
        var ask = "Would you answer 4 questions for us? <a id='task-link' target='_blank' href='" + surveyLink + "'>Open the survey in a new tab</a> and fill it out when you're done on the site. Thanks!";

        // open notification
        var notification = mdn.Notifier.growl(ask, {closable: true, duration: 0}).question();

        // don't ask task completion again for 30 days
        localStorage.setItem('taskTracker', Date.now() + (1000*60*60*24)*30);

        // get ga to append the clientId once it has initialized
        ga(function(tracker) {
            var clientId = tracker.get('clientId');
            surveyLink += '&c=' + clientId;
            $('#task-link').attr('href', surveyLink);
        });

        // listen for clicks
        $('#task-link').on('click', function() {
            ga('send', 'event', 'survey', 'prompt', 'participate', {
                nonInteraction: false
            });

            // dismiss notification after click
            notification.success('We look forward to your feedback!', 2000);
        });
    }

})(window, document, jQuery);
