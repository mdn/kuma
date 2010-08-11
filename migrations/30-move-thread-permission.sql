INSERT INTO authority_permission
    VALUES 
        (NULL,'forums_forum.thread_move_forum',
            (select id from django_content_type where app_label='forums' and model='forum'),1,NULL,1,47963,1,
            '2010-08-10 10:37:22','2010-08-10 10:39:57'),
        (NULL,'forums_forum.thread_move_forum',
            (select id from django_content_type where app_label='forums' and model='forum'),2,NULL,1,47963,1,
            '2010-08-10 10:37:22','2010-08-10 10:39:57'),
        (NULL,'forums_forum.thread_move_forum',
            (select id from django_content_type where app_label='forums' and model='forum'),3,NULL,1,47963,1,
            '2010-08-10 10:37:22','2010-08-10 10:39:57');
