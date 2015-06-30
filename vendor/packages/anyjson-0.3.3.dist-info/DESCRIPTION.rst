##############################
anyjson - JSON library wrapper
##############################

Overview
--------

Anyjson loads whichever is the fastest JSON module installed and provides
a uniform API regardless of which JSON implementation is used.

Originally part of carrot (http://github.com/ask/carrot/)

Examples
--------

To serialize a python object to a JSON string, call the `serialize` function:

>>> import anyjson
>>> anyjson.serialize(["test", 1, {"foo": 3.141592}, "bar"])
'["test", 1, {"foo": 3.141592}, "bar"]'

Conversion the other way is done with the `deserialize` call.

>>> anyjson.deserialize("""["test", 1, {"foo": 3.141592}, "bar"]""")
['test', 1, {'foo': 3.1415920000000002}, 'bar']

Regardless of the JSON implementation used, the exceptions will be the same.
This means that trying to serialize something not compatible with JSON
raises a TypeError:

>>> anyjson.serialize([object()])
Traceback (most recent call last):
  <snipped traceback>
TypeError: object is not JSON encodable

And deserializing a JSON string with invalid JSON raises a ValueError:

>>> anyjson.deserialize("""['missing square brace!""")
Traceback (most recent call last):
  <snipped traceback>
ValueError: cannot parse JSON description


Contact
-------

The module is maintaned by Rune F. Halvorsen <runefh@gmail.com>.
The project resides at http://bitbucket.org/runeh/anyjson . Bugs and feature
requests can be submitted there. Patches are also very welcome.

Changelog
---------

See CHANGELOG file

License
-------

see the LICENSE file


