INSERT IGNORE INTO auth_user_groups (id, user_id, group_id)
  SELECT NULL, users_users.userId, 1
  FROM users_users, users_usergroups
  WHERE users_users.userId = users_usergroups.userId
        AND users_usergroups.groupName = 'Forum Moderators';

INSERT INTO authority_permission
  VALUES
  (NULL,'forums_forum.thread_edit_forum',14,1,NULL,1,47963,1,
   '2010-05-20 10:37:22','2010-05-20 10:39:57'),
  (NULL,'forums_forum.thread_delete_forum',14,1,NULL,1,47963,1,
   '2010-05-20 10:37:22','2010-05-20 10:37:22'),
  (NULL,'forums_forum.thread_sticky_forum',14,1,NULL,1,47963,1,
   '2010-05-20 10:37:22','2010-05-20 10:37:22'),
  (NULL,'forums_forum.post_edit_forum',14,1,NULL,1,47963,1,
   '2010-05-20 10:37:22','2010-05-20 10:37:22'),
  (NULL,'forums_forum.post_delete_forum',14,1,NULL,1,47963,1,
   '2010-05-20 10:37:22','2010-05-20 10:37:22');

UPDATE auth_user
  SET is_superuser = 1, is_staff = 1
  WHERE id IN (SELECT users_users.userId
               FROM users_users, users_usergroups
               WHERE users_users.userId = users_usergroups.userId
                     AND users_usergroups.groupName = 'System Admins');
