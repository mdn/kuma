(function() {
    $(document).ready(function() {
        var $status = $('#chat-status'),
            server = $status.data('server'),
            statusUrl = $status.data('status'),
            startUrl = '/webchat/start.jsp?workgroup=support@workgroup.chat-support.mozilla.com&location=http://bk-sumo.khan.mozilla.org/en-US/kb/Live+chat',
            openImage = '/media/img/chat/foxkeh-open.png',
            closedImage = '/media/img/chat/foxkeh-closed.png',
            $header = $('<h1>'),
            img = new Image(),
            $infoList = $('<ul id="chat-queue-info">'),
            $container = $('<div>');
        img.height = img.width = 200;

        function checkQueueStatus() {

            $.ajax({
                url: statusUrl,
                success: function updateQueueStatus (data, textStatus, xhr) {
                    $status.html('');
                    $infoList.html('');
                    $container.html('');
                    // populated the $status element.
                    var queueStatus = {};
                    $(data).find('stat').each(function() {
                        var k = $(this).attr('name'),
                            v = $(this).text();
                        queueStatus[k] = v;
                    });

                    switch(queueStatus['status']) {
                        case 'OPEN':
                            // queue is open and accepting new chats.
                            $header.text(gettext("We're open!"));
                            img.src = openImage;
                            img.alt = gettext('Our volunteers are ready to help.');
                            var $online = $('<li>').text(gettext('Helpers online: ') + queueStatus['active-agents']),
                                $inQueue = $('<li>').text(gettext('Users waiting: ') + queueStatus['requests-waiting']),
                                $waitTime = $('<li>').text(gettext('Estimated wait: ') + getTimeDisplay(queueStatus['longest-wait'])),
                                $start = $('<a>').attr('href', server+startUrl);

                            $start.click(function(evt) {
                                window.open($start.attr('href'), 'chat-frame',
                                            'height=400,width=500,menubar=no,toolbar=no,location=no,status=no,scrollbars=no');
                                evt.preventDefault();
                                evt.returnValue = false;
                                return false;
                            });

                            var $startImg = $start.clone(true);
                            $startImg.append(img);
                            $start.text(gettext('Start your Live Chat session.'));

                            $container.append($header, $start);
                            $infoList.append($online, $inQueue, $waitTime);

                            $status.append($container, $startImg, $infoList);
                            break;
                        case 'FULL':
                            // queue is open but full.
                            $header.text(gettext('The queue is full.'));
                            $container.append($header);
                            img.src = openImage;
                            img.alt = gettext('Our volunteers are busy helping other users.');
                            var $waitTime = $('<li>').text(gettext('Estimated wait: ') + getTimeDisplay(queueStatus['longest-wait']));
                            $infoList.append($waitTime);
                            $status.append($container, img, $infoList);
                            break;
                        case 'CLOSED':
                        case 'READY':
                        default:
                            // queue is effectively closed.
                            $header.text(gettext("We're closed."));
                            $container.append($header);
                            img.src = closedImage;
                            img.alt = gettext('Live Chat is currently closed.');
                            $status.append($container, img);
                    }
                },
                dataType: 'xml',
                cache: false,
                error: function statusError(xhr, text, e) {
                    $status.html('');
                    $infoList.html('');
                    $container.html('');
                    $header.text(gettext('There was an error checking the queue.'));
                    $container.append($header);
                    $status.append($container);
                }
            });
        }
        checkQueueStatus();

        setInterval(checkQueueStatus, 60000);
    });

    function getTimeDisplay(time) {
        var minutes = Number(time.split(/:/)[0]);
        if ( minutes < 2 ) {
            return gettext('Less than 2 minutes.');
        } else if ( minutes >= 20 ) {
            return gettext('More than 20 minutes.');
        }
        return time;
    }
})();
