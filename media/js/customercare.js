memory = {
    _id: null,
    _name: 'custcare_persist_reply',

    get id() { 
        if (!this._id) {
            if (Modernizr.localstorage)
                this._id = localStorage[this._name];
            else
                this._id = $.cookie(this._name);
        }

        return parseInt(this._id);
    },
    set id(val) {
        this._id = val;
    
        if (Modernizr.localstorage)
            localStorage[this._name] = this._id;
        else
            $.cookie(this._name, this._id);
    },
    del: function () {
        if (Modernizr.localstorage)
            localStorage.removeItem(this._name);
        else
            $.cookie(this._name, null);
    }
}

function Tweet(target) {
    this.$el = $(target);
    this.$username_el = this.$el.find('.twittername');
    this.$content_el = this.$el.find('.text');
    this.$avatar_el = this.$el.find('.avatar');
}
Tweet.prototype = {
    get id() {
        return this.$el.attr('data-tweet-id');
    },
    set id(id) {
        this.$el.attr('data-tweet-id', id);
    },
    get avatar() {
        return {
            href: this.$avatar_el.attr('href'),
            src: this.$avatar_el.find('img').attr('src'),
        }; 
    },
    set avatar(avatar) {
        this.$avatar_el.attr('href', avatar.href);
        this.$avatar_el.find('img').attr('src', avatar.src);
    },
    get username() {
        return this.$username_el.text();
    },
    set username(name) {
        this.$username_el.text(name);
    },
    get content() {
        return this.$content_el.text();
    },
    set content(content) {
        this.$content_el.text(content);
    },
    set_from_tweet: function(tweet) {
        this.id = tweet.id;
        this.avatar = tweet.avatar;
        this.username = tweet.username;
        this.content = tweet.content;
    },
};

$(document).ready(function() {

    $('#accordion').accordion({
        'icons': false,
        'autoHeight': false,
        'collpsible': true,
        'active': false,
    });

    reply = {
        $el: $("#reply-modal"),
        get content() {
            return this.$textarea.val();
        },
        set content(text) {
            text = '@'+ this._tweet.username +' '+ text +' #fxhelp';
            this.$textarea.val(text);
            // trigger keydown so the character counter updates
            this.$textarea.trigger('keydown');
        },
        get tweet() {
            return this._tweet;
        },
        set tweet(tweet) {
            this._tweet.set_from_tweet(tweet);
        },
        init: function() {
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
                'close': function() { modal.reset() },
            };

            this.$el.find('#submit').bind('click', {reply: this}, function(e) {
                var reply = e.data.reply;
                var data = { 
                    'content': reply.content,
                    'reply_to': reply.tweet.id,
                };

                $.ajax({
                    url: reply.action, 
                    data: data, 
                    type: 'POST',
                    success: function(data) {
                        reply.$success_msg.show();
                        setTimeout(function() {
                            reply.close()
                        }, 2000);
                    },
                    error: function(data) {
                        reply.$error_msg.text(data.responseText);
                        reply.$error_msg.show();
                        setTimeout(function() {
                            reply.$error_msg.fadeOut();
                        }, 4000);
                    },
                });
                e.preventDefault();
                return false;
            });
        },
        open: function(tweet) {
            this.tweet = tweet;
            this.content = '';
            this.$el.dialog(this.dialog_options);
            this.$textarea.focus();
        },
        close: function() {
            this.$el.dialog('close');
        },
        reset: function() {
            this.content = '';
            this.$success_msg.hide();
        },
    };
    reply.init();

    var signin = {
        dialog_options: {
            'modal': 'true',
            'position': 'top',
            'width': 500,
        },
        init: function() {
            this.$el = $("#twitter-modal");

            this.$el.find('.cancel').bind('click', {dialog: this.$el}, function(e) {
                e.data.dialog.dialog('close');
                e.preventDefault();
                return false;
            });

        },
        open: function(tweet) {
            this.$el.find('.signin').bind('click', {tweet: tweet}, function(e) {
                memory.id = e.data.tweet.id;
            });
            this.$el.dialog(this.dialog_options);
        },
        close: function() {
            this.$el.dialog('close');
        },
        get authed() {
            return (this.$el.attr('data-authed') == 'True');
        },
    }
    signin.init();

    $('.tweet').live('click', function() {
        var t = new Tweet(this);

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

    $('#refresh-tweets').click(function(e) {
        $("#refresh-busy").show();
        $.get(
            $(this).attr('href'), {},
            function(data) {
                $('#tweets').fadeOut('fast', function() {
                    $(this).html(data).fadeIn();
                    $("#refresh-busy").hide();
                });
            }
        ); 
        e.preventDefault();
        return false;
    });
});
