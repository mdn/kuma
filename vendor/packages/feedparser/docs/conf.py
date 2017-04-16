# project information
project = u'feedparser'
copyright = u'2004-2008 Mark Pilgrim, 2010-2012 Kurt McKee'
version = u'5.1.3'
release = u'5.1.3'
language = u'en'

# documentation options
master_doc = 'index'
exclude_patterns = ['_build']

# use a custom extension to make Sphinx add a <link> to feedparser.css
import sys, os.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
extensions = ['add_custom_css']

# customize the html
# files in html_static_path will be copied into _static/ when compiled
html_static_path = ['_static']
