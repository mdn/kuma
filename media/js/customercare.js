(function($){

    function Memory(name) {
        this._id = null;
        this._name = name;

        this.__defineGetter__('id', function() {
            if (!this._id) {
                if (Modernizr.localstorage) {
                    this._id = localStorage[this._name];
                } else {
                    this._id = $.cookie(this._name);
                }
            }

            return parseInt(this._id, 10);
        });
        this.__defineSetter__('id', function(val) {
            this._id = val;

            if (Modernizr.localstorage) {
                localStorage[this._name] = this._id;
            } else {
                $.cookie(this._name, this._id);
            }
        });

        this.del = function() {
            if (Modernizr.localstorage) {
                localStorage.removeItem(this._name);
            } else {
                $.cookie(this._name, null);
            }
        };
    }
    var memory = new Memory('custcare_persist_reply');

    function Tweet(target) {
        this.$el = $(target);
        this.$username_el = this.$el.find('.twittername').first();
        this.$content_el = this.$el.find('.text').first();
        this.$avatar_el = this.$el.find('.avatar').first();

        this.__defineGetter__('id', function() {
            return this.$el.data('tweet-id');
        });
        this.__defineSetter__('id', function(val) {
            this.$el.data('tweet-id', val);
        });

        this.__defineGetter__('avatar', function() {
            return {
                href: this.$avatar_el.attr('href'),
                src: this.$avatar_el.find('img').attr('src'),
            };
        });
        this.__defineSetter__('avatar', function(val) {
            this.$avatar_el.attr('href', val.href);
            this.$avatar_el.find('img').attr('src', val.src);
        });

        this.__defineGetter__('username', function() {
            return this.$username_el.text();
        });
        this.__defineSetter__('username', function(val) {
            this.$username_el.text(val);
        });

        this.__defineGetter__('content', function() {
            return this.$content_el.text();
        });
        this.__defineSetter__('content', function(val) {
            this.$content_el.text(val);
        });

        this.__defineGetter__('$permalink_el', function() {
            return this.$el.find('.permalink').first();
        });
        this.__defineSetter__('$permalink_el', function($val) {
            this.$el.find('.permalink').first().replaceWith($val.clone());
        });

        this.set_from_tweet = function(tweet) {
            this.id = tweet.id;
            this.avatar = tweet.avatar;
            this.username = tweet.username;
            this.content = tweet.content;
            this.$permalink_el = tweet.$permalink_el;
        };
    }

    // Return the text of the selected region of the HTML document; '' if none.
    // Based on http://www.quirksmode.org/dom/range_intro.html
    function selectedText() {
        var selection = '';
        if (window.getSelection) {
            selection = window.getSelection();
        } else if (document.selection) {  // Opera
            selection = document.selection.createRange();
        }
        if (selection.text) {
            selection = selection.text;
        } else if (selection.toString) {
            selection = selection.toString();
        }
        return selection;
    }

    $(document).ready(function() {

        $('#accordion').accordion({
            'icons': false,
            'autoHeight': false,
            'collapsible': true,
            'active': false,
        });

        function Reply() {

            this.__defineGetter__('content', function() {
                return this.$textarea.val();
            });
            this.__defineSetter__('content', function(val) {
                val = '@'+ this._tweet.username +' '+ val +' #fxhelp';
                this.$textarea.val(val);
                // trigger keydown so the character counter updates
                this.$textarea.trigger('keydown');
            });

            this.__defineGetter__('tweet', function() {
                return this._tweet;
            });
            this.__defineSetter__('tweet', function(val) {
                this._tweet.set_from_tweet(val);
            });

            this.open = function(tweet) {
                this.tweet = tweet;
                this.content = '';
                this.$el.dialog(this.dialog_options);
                var pos = this.$textarea.val().length - 8; // == ' #fxhelp'.length
                this.$textarea.get(0).setSelectionRange(pos, pos);
                this.$textarea.focus();
            };
            this.close = function() {
                this.$el.dialog('close');
            };
            this.reset = function() {
                this.content = '';
                this.$success_msg.hide();
            };

            this.$el = $("#reply-modal");

            this.$tweet_el = this.$el.find("#initial-tweet");
            this._tweet = new Tweet(this.$tweet_el);

            this.$textarea = this.$el.find("#reply-message");
            this.$textarea.NobleCount('.character-counter');

            this.action = this.$el.find("form").attr('action');
            this.$success_msg = this.$el.find("#submit-message");
            this.$error_msg = this.$el.find("#error-message");

            var modal = this;
            this.dialog_options = {
                'modal': true,
                'position': 'top',
                'width': 500,
                'close': function() {
                    modal.reset();
                },
            };

            this.$el.find('#submit').bind('click', {reply: this}, function(e) {
                var reply = e.data.reply,
                    data = {
                        'content': reply.content,
                        'reply_to': reply.tweet.id,
                    },
                    $btn = $(this);
                if (!$btn.is('.busy')) {
                    $btn.addClass('busy');
                    $.ajax({
                        url: reply.action,
                        data: data,
                        type: 'POST',
                        success: function(data) {
                            reply.$success_msg.show();
                            setTimeout(function() {
                                reply.close();
                            }, 2000);

                            appendReply(data, reply.tweet.id);
                        },
                        error: function(data) {
                            reply.$error_msg.text(data.responseText);
                            reply.$error_msg.show();
                            setTimeout(function() {
                                reply.$error_msg.fadeOut();
                            }, 4000);
                        },
                        complete: function() {
                            $btn.removeClass('busy');
                        }
                    });
                }
                e.preventDefault();
                return false;
            });
        }
        var reply = new Reply();

        function Signin() {
            this.open = function(tweet) {
                if (tweet) {
                    this.$el
                        .find('.signin')
                        .bind('click', {tweet: tweet}, function(e) {
                            memory.id = e.data.tweet.id;
                        });
                }
                this.$el.dialog(this.dialog_options);
            };

            this.close = function() {
                this.$el.dialog('close');
            };

            this.__defineGetter__('authed', function() {
                return (this.$el.data('authed') == 'True');
            });

            this.dialog_options = {
                'modal': 'true',
                'position': 'top',
                'width': 500,
            };
            this.$el = $("#twitter-modal");
            this.$el.find('.cancel').bind('click', {dialog: this.$el}, function(e) {
                e.data.dialog.dialog('close');
                e.preventDefault();
                return false;
            });
        }
        var signin = new Signin();

        // Update the "Such and such replied" link text and formatting based on
        // the data-count attr of a parent tweet.
        function update_reply_indicator($parent) {
            var reply_txt = $parent.find('.reply_count').first(),  // first() avoids nested tweets.
                count = reply_txt.data('count') - 1;
            reply_txt.addClass('you');
            if (count === 0) {
                reply_txt.text('You replied');
            } else if (count === 1) {
                reply_txt.text('You and 1 other replied');
            } else {
                reply_txt.text('You and '+count+' others replied');
            }
        }

        // Append a new tweet, given as the HTML of an <li>, to this thread.
        function appendReply(html, parentId) {
            var $parent = $('#tweet-' + parentId),
                $count,
                $replyList = $('#replies_' + parentId).children('ul');
            $replyList.append($(html).hide());

            $count = $parent.find('.reply_count').first();
            if ($count.is('span')) {
                var $zeroCount = $('<a href="#" class="reply_count you" data-count="0"></a>');
                $count.replaceWith($zeroCount);
                $count = $zeroCount;
            }
            $count.addClass('opened')
                  .data('count', parseInt($count.data('count')) + 1);
            $parent.children('.replies:hidden').slideDown();

            update_reply_indicator($parent);

            $replyList.children().last().slideDown();
        }

        /** Mark the tweets that the logged-in user has replied to. */
        function mark_my_replies() {
            if (!signin.authed) return;

            var me = $('#twitter-modal').data('twitter-user');
            
            $('#tweets .replies .twittername')
                .filter(function isMe() { 
                    return $(this).text() == me; })
                .closest('div.replies')  // Walk up to parent.
                .closest('li.tweet')
                .each(function() {
                    update_reply_indicator($('#tweet-' + $(this).data('tweet-id'))); });
        }
        mark_my_replies();

        $('.tweet-contents').live('click', function(e) {
            // Do not open tweet window if clicked on link.
            if ($(e.target).is('a') || $(e.target).parentsUntil('div.tweet-contents').is('a')) {
                return;
            }

            // Allow for selecting the text of a tweet without popping up a
            // dialog. We could do all kinds of mouseup/mousedown gymnastics,
            // but it's simpler and sufficient to see if the selection is
            // empty, assuming that selecting is the only use case for dragging
            // within a tweet. This doesn't allow for double-click-and-drag,
            // unfortunately, but neither would mouseup/mousedown magic.
            if (selectedText().length) {
                return;
            }

            var t = new Tweet($(this).closest('li'));

            if (!signin.authed) {
                signin.open(t);
            } else {
                reply.open(t);
            }
        });

        if (signin.authed && memory.id) {
            $('#tweet-'+ memory.id).trigger('click');
            memory.del();
        }

        $('.reply-topic').click(function(e) {
            reply.content = $(this).next('.snippet').text();
            e.preventDefault();
            return false;
        });


        $(".ui-widget-overlay").live("click", function() {
            reply.close();
            signin.close();
        });

        /** Signin button */
        $('#signin-button').click(function(e) {
            signin.open(null);
            e.preventDefault();
        });


        /** Refresh button */
        $('#refresh-tweets').click(function(e) {
            $("#refresh-busy").show();
            $.get(
                $(this).attr('href'), {},
                function(data) {
                    $('#tweets').fadeOut('fast', function() {
                        $(this).html(data).fadeIn();
                        mark_my_replies();
                        $("#refresh-busy").hide();
                    });
                }
            );
            e.preventDefault();
            return false;
        });

        /* Show/hide replies */
        $('#tweets a.reply_count').live('click', function(e) {
            var to_show = !$(this).hasClass('opened'),
                tweet_id = $(this).closest('li').data('tweet-id'),
                replies = $('#replies_'+tweet_id);
            if (to_show) {
                replies.slideDown();
            } else {
                replies.slideUp();
            }
            $(this).toggleClass('opened');

            $(this).blur();
            e.preventDefault();
        });

        /* Search box */
        $('#side-search input[name="q"]').autoPlaceholderText();

        /* Infinite scrolling */
        $('#infinite-scroll').bind('enterviewport', function() {
            $('#scroll-busy').show();

            var max_id = $('#tweets li:last').data('tweet-id');
            if (!max_id) return;

            $.get(
                $('#refresh-tweets').attr('href'), {max_id: max_id},
                function(data) {
                    if (data) {
                        $('#tweets').append(data);
                        mark_my_replies();
                    } else {
                        // No data left, remove infinite scrolling.
                        $('#infinite-scroll').unbind('enterviewport');
                    }
                    $('#scroll-busy').hide();
                }
            );
        }).bullseye();

        /* Statistics */
        $('#side-stats select').change(function(e) {
            var $this = $(this),
                option = $this.children('option[value=' + $this.val() + ']'),
                bubble = $('#side-stats .bubble')
                contribs = $('#side-stats .contribs');
            // Update numbers
            bubble.find('.perc .data').text(option.data('perc'));
            bubble.find('.replies .data').text(option.data('replies'));
            bubble.find('.tweets .data').text(option.data('requests'));

            // Update contributors
            contribs.find('.contributors:visible').fadeOut('fast', function() {
                contribs.find('.contributors.period' + $this.val()).fadeIn('fast');
            });

            $this.blur();
            e.preventDefault();
        }).val('0');
    });
}(jQuery));
