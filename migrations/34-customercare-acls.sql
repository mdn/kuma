INSERT IGNORE INTO `django_content_type` (`name`, `app_label`, `model`) VALUES 
('tweet', 'customercare', 'tweet'),
('canned category', 'customercare', 'cannedcategory'),
('canned response', 'customercare', 'cannedresponse'),
('category membership', 'customercare', 'categorymembership');

SET @tweet_ct = (SELECT `id` FROM `django_content_type` WHERE `name` = 'tweet'); 
SET @canned_cat_ct = (SELECT `id` FROM `django_content_type` WHERE `name` = 'canned category');
SET @canned_resp_ct = (SELECT `id` FROM `django_content_type` WHERE `name` = 'canned response');
SET @cat_member_ct = (SELECT `id` FROM `django_content_type` WHERE `name` = 'category membership');

INSERT IGNORE INTO `auth_permission` (`name`, `content_type_id`, `codename`) VALUES 
('Can add tweet', @tweet_ct, 'add_tweet'),
('Can change tweet', @tweet_ct, 'change_tweet'),
('Can delete tweet', @tweet_ct, 'delete_tweet'),
('Can add canned category', @canned_cat_ct, 'add_cannedcategory'),
('Can change canned category', @canned_cat_ct, 'change_cannedcategory'),
('Can delete canned category', @canned_cat_ct, 'delete_cannedcategory'),
('Can add canned response', @canned_resp_ct, 'add_cannedresponse'),
('Can change canned response', @canned_resp_ct, 'change_cannedresponse'),
('Can delete canned response', @canned_resp_ct, 'delete_cannedresponse'),
('Can add category membership', @cat_member_ct, 'add_categorymembership'),
('Can change category membership', @cat_member_ct, 'change_categorymembership'),
('Can delete category membership', @cat_member_ct, 'delete_categorymembership');
