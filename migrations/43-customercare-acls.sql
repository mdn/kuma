INSERT IGNORE INTO `django_content_type` (`name`, `app_label`, `model`) VALUES 
('tweet', 'customercare', 'tweet'),
('canned category', 'customercare', 'cannedcategory'),
('canned response', 'customercare', 'cannedresponse'),
('category membership', 'customercare', 'categorymembership');

INSERT IGNORE INTO `auth_permission` (`name`, `content_type_id`, `codename`) VALUES 
('Can add tweet', 36, 'add_tweet'),
('Can change tweet', 36, 'change_tweet'),
('Can delete tweet', 36, 'delete_tweet'),
('Can add canned category', 37, 'add_cannedcategory'),
('Can change canned category', 37, 'change_cannedcategory'),
('Can delete canned category', 37, 'delete_cannedcategory'),
('Can add canned response', 38, 'add_cannedresponse'),
('Can change canned response', 38, 'change_cannedresponse'),
('Can delete canned response', 38, 'delete_cannedresponse'),
('Can add category membership', 39, 'add_categorymembership'),
('Can change category membership', 39, 'change_categorymembership'),
('Can delete category membership', 39, 'delete_categorymembership');
