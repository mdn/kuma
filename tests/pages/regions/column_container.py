from pypom import Region
from selenium.webdriver.common.by import By


class ColumnContainer(Region):

    # TODO: needs to exclude child columns, should only be checking 1 deep
    _column_locator = (By.CSS_SELECTOR, '[class^="column-"]')

    # TODO: handle reversed columns
    # TODO: needs desktop vs mobile approach
    def is_expected_stacking(self):
        # get all columns
        columns = self.find_elements(*self._column_locator)
        # loop through
        last_x = None
        last_y = None
        for column in columns:
            this_x = column.location['x']
            this_y = column.location['y']
            if last_x != None and last_x <= this_x:
                print 'column x values should be acending'
                return False
            if last_y != None and last_y == this_y:
                print 'column y values should all match'
                return False
            print type(this_x)

        return True
