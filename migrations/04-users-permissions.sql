-- Migrate the users first
INSERT IGNORE INTO auth_user (id, username, first_name, last_name,
                              email, password, is_staff, is_active,
                              is_superuser, last_login, date_joined)
  SELECT users_users.userId, users_users.login, '', '',
         users_users.email, '', 0, 1, 0,
         FROM_UNIXTIME(users_users.registrationDate),
         FROM_UNIXTIME(users_users.registrationDate)
  FROM users_users;

INSERT INTO auth_group (id, name)
  VALUES (1, 'Forum Moderators');

UPDATE auth_user SET password = '';
