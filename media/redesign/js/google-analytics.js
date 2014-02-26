(function($) {
  'use strict';

  /*
  https://github.com/mozilla/bedrock/blob/master/media/js/base/global.js#L176
  */
  function gaTrack(eventArray, callback) {
    // submit eventArray to GA and call callback only after tracking has
    // been sent, or if sending fails.
    //
    // callback is optional.
    //
    // Example usage:
    //
    // $(function() {
    //      var handler = function(e) {
    //           var _this = this;
    //           e.preventDefault();
    //           $(_this).off('submit', handler);
    //           gaTrack(
    //              ['_trackEvent', 'Newsletter Registration', 'submit', newsletter],
    //              function() {$(_this).submit();}
    //           );
    //      };
    //      $(thing).on('submit', handler);
    // });

    var timer = null;
    var hasCallback = typeof(callback) === 'function';
    var gaCallback;

    // Only build new function if callback exists.
    if (hasCallback) {
      gaCallback = function() {
        clearTimeout(timer);
        callback();
      };
    }
    if (typeof(window._gaq) === 'object') {
      // send event to GA
      window._gaq.push(eventArray);
      // Only set up timer and hitCallback if a callback exists.
      if (hasCallback) {
        // Failsafe - be sure we do the callback in a half-second
        // even if GA isn't able to send in our trackEvent.
        timer = setTimeout(gaCallback, 500);

        // But ordinarily, we get GA to call us back immediately after
        // it finishes sending our things.
        // https://developers.google.com/analytics/devguides/collection/gajs/#PushingFunctions
        // This is called after GA has sent the current pending data:
        window._gaq.push(gaCallback);
      }
    } else {
      // GA disabled or blocked or something, make sure we still
      // call the caller's callback:
      if (hasCallback) {
          callback();
      }
    }
  }

  /*
  Track all outgoing links
  */
  $('body').on('click', 'a', function (e) {
    if (this.hostname === window.location.hostname ||
        this.protocol == 'javascript:') {
      return;
    }
    var newTab = (this.target === '_blank' || e.metaKey || e.ctrlKey);
    var href = this.href;
    var callback = function() {
      window.location = href;
    };

    var data = ['_trackEvent', 'Outbound Links', href]; 
    if (newTab) {
      gaTrack(data);
    } else {
      e.preventDefault();
      gaTrack(data, callback);
    }
  });

})(jQuery);
