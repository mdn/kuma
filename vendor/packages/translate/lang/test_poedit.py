from translate.lang.poedit import isocode


def test_isocode():
    """Test the isocode function"""
    # Standard lookup
    assert isocode("French") == "fr"
    # Dialect lookups: Portuguese
    assert isocode("Portuguese") == "pt"  # No country we default to 'None'
    assert isocode("Portuguese", "BRAZIL") == "pt_BR"  # Country with a valid dialect
    assert isocode("Portuguese", "PORTUGAL") == "pt"
    assert isocode("Portuguese", "MOZAMBIQUE") == "pt"  # Country is not a dialect so use default
    # Dialect lookups: English
    assert isocode("English") == "en"
    assert isocode("English", "UNITED KINGDOM") == "en_GB"
    assert isocode("English", "UNITED STATES") == "en"
