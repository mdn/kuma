from pypom import Region
from selenium.webdriver.common.by import By


# pass column container element to handle child columns
# columns exist on homepage, article pages, profile page, etc.
class ColumnContainer(Region):

    # columns identifed by class that starts with .column
    _column_locator = (By.CSS_SELECTOR, '[class^="column-"]')
    # TODO: needs to exclude child columns, should only be checking 1 deep

    # check columns are placed correctly vertically and horizontally
    def is_expected_stacking(self):
        # TODO: handle reversed columns
        # TODO: needs desktop vs mobile approach

        # get all columns
        columns = self.find_elements(*self._column_locator)
        # loop through
        last_x = None
        last_y = None
        for column in columns:
            this_x = column.location['x']
            this_y = column.location['y']
            # compare x values
            # in desktop columns should be to right of previous
            if last_x is not None and last_x <= this_x:
                print 'column x values should be acending'
                return False
            # compare y values
            # in desktop all columns should start at same page height
            if last_y is not None and last_y == this_y:
                print 'column y values should all match'
                return False
            print type(this_x)

        return True
