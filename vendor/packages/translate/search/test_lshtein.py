from translate.search import lshtein


class TestLevenshtein:
    """Test whether Levenshtein distance calculations are correct"""

    def test_basic_distance(self):
        """Tests distance correctness with a few basic values"""
        levenshtein = lshtein.LevenshteinComparer()
        assert lshtein.distance("word", "word") == 0
        assert lshtein.distance("word", "") == 4
        assert lshtein.distance("", "word") == 4
        assert lshtein.distance("word", "word 2") == 2
        assert lshtein.distance("words", "word") == 1
        assert lshtein.distance("word", "woord") == 1

    def test_basic_similarity(self):
        """Tests similarity correctness with a few basic values"""
        levenshtein = lshtein.LevenshteinComparer()
        assert levenshtein.similarity("word", "word") == 100
        assert levenshtein.similarity("word", "words") == 80
        assert levenshtein.similarity("word", "wood") == 75
        assert levenshtein.similarity("aaa", "bbb", 0) == 0

    def test_long_similarity(self):
        """Tests that very long strings are handled well."""
        #A sentence with 240 characters:
        sentence = "A long, dreary sentence about a cow that never new his mother. Actually it didn't known its father either. One day he decided that enough is enough, and that he would stop making long, dreary sentences just for the sake of making sentences."
        levenshtein = lshtein.LevenshteinComparer()
        assert levenshtein.similarity("Cow", sentence, 10) < 10
        assert levenshtein.similarity(sentence, "Cow", 10) < 10
        #The difference in the next comparison is supposed to be 25.83, but
        #since the sentence is long it might be chopped and report higher.
        assert levenshtein.similarity(sentence, sentence[0:62], 0) > 25
        assert levenshtein.similarity(sentence, sentence[0:62], 0) < 50
