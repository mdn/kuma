-- Remove old, insecure password hashes.
UPDATE
    auth_user
SET
    password = 'PASSWORD_DISABLED'
WHERE
    password NOT LIKE 'sha%';
