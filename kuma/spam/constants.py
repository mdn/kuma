import re

VERIFY_URL_RE = re.compile(r'https://.*\.rest\.akismet\.com/1\.1/verify-key')
CHECK_URL_RE = re.compile(r'https://.*\.rest\.akismet\.com/1\.1/comment-check')
SPAM_URL_RE = re.compile(r'https://.*\.rest\.akismet\.com/1\.1/submit-spam')
HAM_URL_RE = re.compile(r'https://.*\.rest\.akismet\.com/1\.1/submit-ham')

SPAM_CHECKS_FLAG = 'spam_checks_enabled'
