"""illustrates a quick and dirty way to persist an XML document expressed using ElementTree and pickle.

This is a trivial example using PickleType to marshal/unmarshal the ElementTree 
document into a binary column.  Compare to explicit.py which stores the individual components of the ElementTree
structure in distinct rows using two additional mapped entities.  Note that the usage of both
styles of persistence are identical, as is the structure of the main Document class.
"""

from sqlalchemy import (create_engine, MetaData, Table, Column, Integer, String,
    PickleType)
from sqlalchemy.orm import mapper, create_session

import sys, os

from xml.etree import ElementTree

engine = create_engine('sqlite://')
meta = MetaData(engine)

# setup a comparator for the PickleType since it's a mutable
# element.
def are_elements_equal(x, y):
    return x == y

# stores a top level record of an XML document.  
# the "element" column will store the ElementTree document as a BLOB.
documents = Table('documents', meta,
    Column('document_id', Integer, primary_key=True),
    Column('filename', String(30), unique=True),
    Column('element', PickleType(comparator=are_elements_equal))
)

meta.create_all()

# our document class.  contains a string name,
# and the ElementTree root element.  
class Document(object):
    def __init__(self, name, element):
        self.filename = name
        self.element = element

# setup mapper.
mapper(Document, documents)

###### time to test ! #########

# get ElementTree document
filename = os.path.join(os.path.dirname(__file__), "test.xml")
doc = ElementTree.parse(filename)
    
# save to DB
session = create_session()
session.add(Document("test.xml", doc))
session.flush()

# clear session (to illustrate a full load), restore
session.expunge_all()
document = session.query(Document).filter_by(filename="test.xml").first()

# print
document.element.write(sys.stdout)

