#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2009 Zuza Software Foundation
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

"""Functions to manage Poedit's language features.

  ISO 639 maps are form Poedit's U{isocode.cpp 1.4.2<http://poedit.svn.sourceforge.net/viewvc/poedit/poedit/tags/release-1.4.2/src/isocodes.cpp?revision=1452&view=markup>}
  to ensure that we match currently released versions of Poedit.
"""

lang_codes = {
    "aa": "Afar",
    "ab": "Abkhazian",
    "ae": "Avestan",
    "af": "Afrikaans",
    "am": "Amharic",
    "ar": "Arabic",
    "as": "Assamese",
    "ay": "Aymara",
    "az": "Azerbaijani",
    "ba": "Bashkir",
    "be": "Belarusian",
    "bg": "Bulgarian",
    "bh": "Bihari",
    "bi": "Bislama",
    "bn": "Bengali",
    "bo": "Tibetan",
    "br": "Breton",
    "bs": "Bosnian",
    "ca": "Catalan",
    "ce": "Chechen",
    "ch": "Chamorro",
    "co": "Corsican",
    "cs": "Czech",
    "cu": "Church Slavic",
    "cv": "Chuvash",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "dz": "Dzongkha",
    "el": "Greek",
    "en": "English",
    "eo": "Esperanto",
    "es": "Spanish",
    "et": "Estonian",
    "eu": "Basque",
    "fa": "Persian",
    "fi": "Finnish",
    "fj": "Fijian",
    "fo": "Faroese",
    "fr": "French",
    "fur": "Friulian",
    "fy": "Frisian",
    "ga": "Irish",
    "gd": "Gaelic",
    "gl": "Galician",
    "gn": "Guarani",
    "gu": "Gujarati",
    "ha": "Hausa",
    "he": "Hebrew",
    "hi": "Hindi",
    "ho": "Hiri Motu",
    "hr": "Croatian",
    "hu": "Hungarian",
    "hy": "Armenian",
    "hz": "Herero",
    "ia": "Interlingua",
    "id": "Indonesian",
    "ie": "Interlingue",
    "ik": "Inupiaq",
    "is": "Icelandic",
    "it": "Italian",
    "iu": "Inuktitut",
    "ja": "Japanese",
    "jw": "Javanese",
    "ka": "Georgian",
    "ki": "Kikuyu",
    "kj": "Kuanyama",
    "kk": "Kazakh",
    "kl": "Kalaallisut",
    "km": "Khmer",
    "kn": "Kannada",
    "ko": "Korean",
    "ks": "Kashmiri",
    "ku": "Kurdish",
    "kv": "Komi",
    "kw": "Cornish",
    "ky": "Kyrgyz",
    "la": "Latin",
    "lb": "Letzeburgesch",
    "ln": "Lingala",
    "lo": "Lao",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mg": "Malagasy",
    "mh": "Marshall",
    "mi": "Maori",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mn": "Mongolian",
    "mo": "Moldavian",
    "mr": "Marathi",
    "ms": "Malay",
    "mt": "Maltese",
    "my": "Burmese",
    "na": "Nauru",
    "ne": "Nepali",
    "ng": "Ndonga",
    "nl": "Dutch",
    "nn": "Norwegian Nynorsk",
    "nb": "Norwegian Bokmal",
    "nr": "Ndebele, South",
    "nv": "Navajo",
    "ny": "Chichewa; Nyanja",
    "oc": "Occitan",
    "om": "(Afan) Oromo",
    "or": "Oriya",
    "os": "Ossetian; Ossetic",
    "pa": "Panjabi",
    "pi": "Pali",
    "pl": "Polish",
    "ps": "Pashto, Pushto",
    "pt": "Portuguese",
    "qu": "Quechua",
    "rm": "Rhaeto-Romance",
    "rn": "Rundi",
    "ro": "Romanian",
    "ru": "Russian",
    "rw": "Kinyarwanda",
    "sa": "Sanskrit",
    "sc": "Sardinian",
    "sd": "Sindhi",
    "se": "Northern Sami",
    "sg": "Sangro",
    "sh": "Serbo-Croatian",
    "si": "Sinhalese",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sm": "Samoan",
    "sn": "Shona",
    "so": "Somali",
    "sq": "Albanian",
    "sr": "Serbian",
    "ss": "Siswati",
    "st": "Sesotho",
    "su": "Sundanese",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "tg": "Tajik",
    "th": "Thai",
    "ti": "Tigrinya",
    "tk": "Turkmen",
    "tl": "Tagalog",
    "tn": "Setswana",
    "to": "Tonga",
    "tr": "Turkish",
    "ts": "Tsonga",
    "tt": "Tatar",
    "tw": "Twi",
    "ty": "Tahitian",
    "ug": "Uighur",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "vo": "Volapuk",
    "wa": "Walloon",
    "wo": "Wolof",
    "xh": "Xhosa",
    "yi": "Yiddish",
    "yo": "Yoruba",
    "za": "Zhuang",
    "zh": "Chinese",
    "zu": "Zulu",
}
"""ISO369 codes and names as used by Poedit.
Mostly these are identical to ISO 639, but there are some differences."""

lang_names = dict([(value, key) for (key, value) in lang_codes.items()])
"""Reversed L{lang_codes}"""

dialects = {
  "Portuguese": {"PORTUGAL": "pt", "BRAZIL": "pt_BR", "None": "pt"},
  # We choose not to subtype en_US
  "English": {"UNITED KINGDOM": "en_GB", "SOUTH AFRICA": "en_ZA", "None": "en"},
  # zh_CN = Simplified, zh_TW = Traditional
  "Chinese": {"CHINA": "zh_CN", "TAIWAN": "zh_TW", "None": "zh_CN"},
}
"""Language dialects based on ISO 3166 country names, 'None' is the default fallback"""

def isocode(language, country=None):
    """Returns a language code for the given Poedit language name.

    Poedit uses language and country names in the PO header entries:
      - X-Poedit-Language
      - X-Poedit-Country

    This function converts the supplied language name into the required ISO 639 
    code. If needed, in the case of L{dialects}, the country name is used
    to create an xx_YY style dialect code.

    @param language: Language name
    @type language: String
    @param country: Country name
    @type country: String
    @return: ISO 639 language code
    @rtype: String
    """
    dialect = dialects.get(language, None)
    if dialect:
        return dialect.get(country, dialect["None"])
    return lang_names.get(language, None)
