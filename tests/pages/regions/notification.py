from pypom import Region
from selenium.webdriver.common.by import By


class NotificationTray(Region):
    _root_locator = (By.CSS_SELECTOR, '.notification-tray')


class Notification(Region):
    _root_locator = (By.CSS_SELECTOR, '.notification')
