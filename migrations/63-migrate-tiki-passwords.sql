-- Set user passwords from Tiki.
UPDATE auth_user a SET password = (SELECT hash FROM users_users u WHERE u.userId = a.id);
