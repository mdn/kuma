#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2004-2008 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""functions to get decorative/informative text out of strings..."""

import re
import unicodedata
from translate.lang import data

def spacestart(str1):
    """returns all the whitespace from the start of the string"""
    newstring = u""
    for c in str1:
        if c.isspace():
            newstring += c
        else:
            break
    return newstring

def spaceend(str1):
    """returns all the whitespace from the end of the string"""
    newstring = u""
    for n in range(len(str1)):
        c = str1[-1-n]
        if c.isspace():
            newstring = c + newstring
        else:
            break
    return newstring

def puncstart(str1, punctuation):
    """returns all the punctuation from the start of the string"""
    newstring = u""
    for c in str1:
        if c in punctuation or c.isspace():
            newstring += c
        else:
            break
    return newstring

def puncend(str1, punctuation):
    """returns all the punctuation from the end of the string"""
    # An implementation with regular expressions was slightly slower.

    newstring = u""
    for n in range(len(str1)):
        c = str1[-1-n]
        if c in punctuation or c.isspace():
            newstring = c + newstring
        else:
            break
    return newstring.replace(u"\u00a0", u" ")

def ispurepunctuation(str1):
    """checks whether the string is entirely punctuation"""
    for c in str1:
        if c.isalnum():
            return False
    return len(str1)

def isvalidaccelerator(accelerator, acceptlist=None):
    """returns whether the given accelerator character is valid

    @type accelerator: character
    @param accelerator: A character to be checked for accelerator validity
    @type acceptlist: String
    @param acceptlist: A list of characters that are permissible as accelerators
    @rtype: Boolean
    @return: True if the supplied character is an acceptable accelerator
    """
    assert isinstance(accelerator, unicode)
    assert isinstance(acceptlist, unicode) or acceptlist is None
    if len(accelerator) == 0:
        return False
    if acceptlist is not None:
        acceptlist = data.normalize(acceptlist)
        if accelerator in acceptlist:
            return True
        return False
    else:
        # Old code path - ensures that we don't get a large number of regressions
        accelerator = accelerator.replace("_","")
        if accelerator in u"-?":
            return True
        if not accelerator.isalnum():
            return False

        # We don't want to have accelerators on characters with diacritics, so let's 
        # see if the character can decompose.
        decomposition = unicodedata.decomposition(accelerator)
        # Next we strip out any extra information like <this>
        decomposition = re.sub("<[^>]+>", "", decomposition).strip()
        return decomposition.count(" ") == 0

def findaccelerators(str1, accelmarker, acceptlist=None):
    """returns all the accelerators and locations in str1 marked with a given marker"""
    accelerators = []
    badaccelerators = []
    currentpos = 0
    while currentpos >= 0:
        currentpos = str1.find(accelmarker, currentpos)
        if currentpos >= 0:
            accelstart = currentpos
            currentpos += len(accelmarker)
            # we assume accelerators are single characters
            accelend = currentpos + 1
            if accelend > len(str1): break
            accelerator = str1[currentpos:accelend]
            currentpos = accelend
            if isvalidaccelerator(accelerator, acceptlist):
                accelerators.append((accelstart, accelerator))
            else:
                badaccelerators.append((accelstart, accelerator))
    return accelerators, badaccelerators

def findmarkedvariables(str1, startmarker, endmarker, ignorelist=[]):
    """returns all the variables and locations in str1 marked with a given marker"""
    variables = []
    currentpos = 0
    while currentpos >= 0:
        variable = None
        currentpos = str1.find(startmarker, currentpos)
        if currentpos >= 0:
            startmatch = currentpos
            currentpos += len(startmarker)
            if endmarker is None:
                # handle case without an end marker - use any non-alphanumeric character as the end marker, var must be len > 1
                endmatch = currentpos
                for n in range(currentpos, len(str1)):
                    if not (str1[n].isalnum() or str1[n] == '_'):
                        endmatch = n
                        break
                if currentpos == endmatch: endmatch = len(str1)
                if currentpos < endmatch:
                    variable = str1[currentpos:endmatch]
                currentpos = endmatch
            elif type(endmarker) == int:
                # setting endmarker to an int means it is a fixed-length variable string (usually endmarker==1)
                endmatch = currentpos + endmarker
                if endmatch > len(str1): break
                variable = str1[currentpos:endmatch]
                currentpos = endmatch
            else:
                endmatch = str1.find(endmarker, currentpos)
                if endmatch == -1: break
                # search backwards in case there's an intervening startmarker (if not it's OK)...
                start2 = str1.rfind(startmarker, currentpos, endmatch)
                if start2 != -1:
                    startmatch2 = start2
                    start2 += len(startmarker)
                    if start2 != currentpos:
                        currentpos = start2
                        startmatch = startmatch2
                variable = str1[currentpos:endmatch]
                currentpos = endmatch + len(endmarker)
            if variable is not None and variable not in ignorelist:
                if not variable or variable.replace("_","").replace(".","").isalnum():
                    variables.append((startmatch, variable))
    return variables

def getaccelerators(accelmarker, acceptlist=None):
    """returns a function that gets a list of accelerators marked using accelmarker"""
    def getmarkedaccelerators(str1):
        """returns all the accelerators in str1 marked with a given marker"""
        acclocs, badlocs = findaccelerators(str1, accelmarker, acceptlist)
        accelerators = [accelerator for accelstart, accelerator in acclocs]
        badaccelerators = [accelerator for accelstart, accelerator in badlocs]
        return accelerators, badaccelerators
    return getmarkedaccelerators

def getvariables(startmarker, endmarker):
    """returns a function that gets a list of variables marked using startmarker and endmarker"""
    def getmarkedvariables(str1):
        """returns all the variables in str1 marked with a given marker"""
        varlocs = findmarkedvariables(str1, startmarker, endmarker)
        variables = [variable for accelstart, variable in varlocs]
        return variables
    return getmarkedvariables

def getnumbers(str1):
    """returns any numbers that are in the string"""
    # TODO: handle locale-based periods e.g. 2,5 for Afrikaans
    assert isinstance(str1, unicode)
    numbers = []
    innumber = False
    degreesign = u'\xb0'
    lastnumber = ""
    carryperiod = ""
    for chr1 in str1:
        if chr1.isdigit():
            innumber = True
        elif innumber:
            if not (chr1 == '.' or chr1 == degreesign):
                innumber = False
                if lastnumber:
                    numbers.append(lastnumber)
                lastnumber = ""
        if innumber:
            if chr1 == degreesign:
                lastnumber += chr1
            elif chr1 == '.':
                carryperiod += chr1
            else:
                lastnumber += carryperiod + chr1
                carryperiod = ""
        else:
            carryperiod = ""
    if innumber:
        if lastnumber:
            numbers.append(lastnumber)
    return numbers

def getfunctions(str1, punctuation):
    """returns the functions() that are in a string, while ignoring the trailing 
    punctuation in the given parameter"""
    punctuation = punctuation.replace("(", "").replace(")", "")
    return [word.rstrip(punctuation) for word in str1.split() if word.rstrip(punctuation).endswith("()")]

def getemails(str1):
    """returns the email addresses that are in a string"""
    return re.findall('[\w\.\-]+@[\w\.\-]+', str1)

def geturls(str1):
    """returns the URIs in a string"""
    URLPAT = 'https?:[\w/\.:;+\-~\%#\$?=&,()]+|www\.[\w/\.:;+\-~\%#\$?=&,()]+|' +\
            'ftp:[\w/\.:;+\-~\%#?=&,]+'
    return re.findall(URLPAT, str1)

def countaccelerators(accelmarker, acceptlist=None):
    """returns a function that counts the number of accelerators marked with the given marker"""
    def countmarkedaccelerators(str1):
        """returns all the variables in str1 marked with a given marker"""
        acclocs, badlocs = findaccelerators(str1, accelmarker, acceptlist)
        return len(acclocs), len(badlocs)
    return countmarkedaccelerators


