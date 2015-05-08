from translate.search import terminology


class TestTerminology:
    """Test terminology matching"""

    def test_basic(self):
        """Tests basic functionality"""
        termmatcher = terminology.TerminologyComparer()
        assert termmatcher.similarity("Open the file", "file") > 75
