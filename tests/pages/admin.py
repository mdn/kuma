from pypom import Page
from selenium.webdriver.common.by import By


class AdminLogin(Page):

    URL_TEMPLATE = '/admin/'

    SUPER_USER = "test-super"
    MODERATOR_USER = "test-moderator"
    NEW_USER = "test-new"
    BANNED_USER = "test-banned"
    SPAM_USER = "viagra-test-123"
    PASSWORD = "test-password"

    _username_field_locator = (By.ID, 'id_username')
    _password_field_locator = (By.ID, 'id_password')
    _login_button_locator = (By.CSS_SELECTOR, '[type="submit"]')

    def login_user(self, username):
        # username
        username_field = self.find_element(*self._username_field_locator)
        username_field.send_keys(username)
        # password
        password_field = self.find_element(*self._password_field_locator)
        password_field.send_keys(self.PASSWORD)
        # click login
        login_button = self.find_element(*self._login_button_locator)
        login_button.click()
        # wait for admin dashboard to load
        self.wait.until(lambda s: 'dashboard' in self.find_element(By.CSS_SELECTOR, 'body').get_attribute('class'))

    def login_super_user(self):
        self.login_user(self.SUPER_USER)

    def login_moderator_user(self):
        self.login_user(self.MODERATOR_USER)

    def login_new_user(self):
        self.login_user(self.NEW_USER)

    def login_banned_user(self):
        self.login_user(self.BANNED_USER)

    def login_spam_user(self):
        self.login_user(self.SPAM_USER)
