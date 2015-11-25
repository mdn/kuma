#!/usr/bin/env python

from translate.misc import progressbar


def test_hashprogressbar():
    """Test the [###   ] progress bar"""
    bar = progressbar.HashProgressBar()
    assert str(bar) == "[                                           ]   0%"
    bar.amount = 50
    assert str(bar) == "[######################                     ]  50%"
    bar.amount = 100
    assert str(bar) == "[###########################################] 100%"
