from nose.tools import eq_

from search.utils import crc32


def test_crc32_ascii():
    """crc32 works for ascii. Integer value taken from mysql's CRC32."""
    eq_(525924414, crc32('teststring'))


def test_crc32_fr():
    """crc32 works for french. Integer value taken from mysql's CRC32."""
    eq_(2750076964, crc32(u'parl\u00e9 Fran\u00e7ais'))


def test_crc32_ja():
    """crc32 works for japanese. Integer value taken from mysql's CRC32."""
    eq_(696255294, crc32(u'\u6709\u52b9'))
