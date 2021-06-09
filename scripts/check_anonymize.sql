/* use developer_mozilla_org; */
SELECT COUNT(*) AS django_admin_log_should_be_zero FROM django_admin_log;
SELECT COUNT(*) AS django_session_should_be_zero FROM django_session;
SELECT COUNT(*) AS djcelery_crontabschedule_should_be_zero FROM djcelery_crontabschedule;
SELECT COUNT(*) AS djcelery_intervalschedule_should_be_zero FROM djcelery_intervalschedule;
SELECT COUNT(*) AS djcelery_periodictask_should_be_zero FROM djcelery_periodictask;
SELECT COUNT(*) AS djcelery_periodictasks_should_be_zero FROM djcelery_periodictasks;
SELECT COUNT(*) AS djcelery_taskstate_should_be_zero FROM djcelery_taskstate;
SELECT COUNT(*) AS djcelery_workerstate_should_be_zero FROM djcelery_workerstate;

SELECT COUNT(password) AS auth_user_password_should_be_zero FROM auth_user WHERE password!='!';
SELECT COUNT(email) as auth_user_email_should_be_zero from auth_user WHERE email not like '%@example.com';
SELECT count(first_name) as auth_user_first_name_should_be_zero FROM auth_user WHERE first_name like '%a%' or first_name like '%b%' or first_name like '%c%' or first_name like '%d%' or first_name like '%e%' or first_name like '%f%' or first_name like '%g%' or first_name like '%h%' or first_name like '%i%' or first_name like '%j%' or first_name like '%k%' or first_name like '%l%' or first_name like '%m%' or first_name like '%n%' or first_name like '%o%' or first_name like '%p%' or first_name like '%q%' or first_name like '%r%' or first_name like '%s%' or first_name like '%t%' or first_name like '%u%' or first_name like '%v%' or first_name like '%w%' or first_name like '%x%' or first_name like '%y%' or first_name like '%z%';
SELECT count(last_name) AS auth_user_last_name_should_be_zero FROM auth_user where last_name like '%a%' or last_name like '%b%' or last_name like '%c%' or last_name like '%d%' or last_name like '%e%' or last_name like '%f%' or last_name like '%g%' or last_name like '%h%' or last_name like '%i%' or last_name like '%j%' or last_name like '%k%' or last_name like '%l%' or last_name like '%m%' or last_name like '%n%' or last_name like '%o%' or last_name like '%p%' or last_name like '%q%' or last_name like '%r%' or last_name like '%s%' or last_name like '%t%' or last_name like '%u%' or last_name like '%v%' or last_name like '%w%' or last_name like '%x%' or last_name like '%y%' or last_name like '%z%';
SELECT COUNT(*) AS auth_user_stripe_customer_id_should_be_zero FROM auth_user where stripe_customer_id!='';

SELECT COUNT(*) AS wiki_revisionip_with_data_should_be_zero FROM wiki_revisionip WHERE data is not null;
