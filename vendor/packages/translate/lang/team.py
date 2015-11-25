#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 Zuza Software Foundation
#
# This file is part of the Translate Toolkit.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Module to guess the language ISO code based on the 'Language-Team' entry in
the header of a Gettext PO file.
"""

import re


__all__ = ['LANG_TEAM_CONTACT_SNIPPETS', 'guess_language']

LANG_TEAM_REGEX = (
   ("@li.org", "([a-z_A-Z]{2,})@li.org", ["LL", "XX", "TEAM"]),
   ("translation-team",
    "translation-team-([a-z_A-Z]+)@lists.sourceforge.net", None),
   ("fedora-trans", "fedora-trans-([a-z_A-Z]+)@redhat.com", ["list"]),
   ("ubuntu-l10n", "ubuntu-l10n-([a-z_A-Z]+)@lists.ubuntu.com", None),
   ("translate-discuss",
    "translate-discuss-([a-z_A-Z]+)@lists.sourceforge.net", None),
   ("kde-i18n", "kde-i18n-([a-z_A-Z]+)@(?:lists\.|mail\.|)kde.org", ["doc"]),
   ("kde-l10n", "kde-l10n-([a-z_A-Z]+)@kde.org", None),
   ("fedoraproject", "trans-([a-z_A-Z]+)@lists.fedoraproject.org", None),
   ("gnome.org", "gnome-([a-z_A-Z]+)-list@gnome.org", ["latin"]),
)
"""Data for regular expression based extraction.  The fieds are: prefilter
information, regex with single group that contains the language code,
postfilter."""

LANG_TEAM_CONTACT_SNIPPETS = {
    "af": ("i18n@af.org.za", "Petri Jooste",),
    "am": ("@geez.org", ),
    "ar": ("arabeyes.org", "Arabeyes", ),
    "as": ("assam@mm.assam-glug.org", ),
    "ast": ("@softastur.org", "launchpad.net/~ubuntu-l10n-ast",
            "softast-xeneral@lists.sourceforge.net", "Softastur",),
    "az": ("linuxaz@azerimal.net", "gnome@azitt.com", u"gnome@azətt.com",),
    "az_IR": ("az-ir@lists.sharif.edu",),
    "be": ("i18n@mova.org", "i18n@tut.by", "mozilla_byx@poczta.fm",),
    "be@latin": ("translation-team-be-latin@lists", "be-latin.open-tran.eu",),
    "bg": ("dict@fsa-bg.org", "dict@linux.zonebg.com", ),
    "bn": ("gnome-translation@bengalinux.org", "core@bengalinux.org",
           "ankur-bd-l10n@googlegroups.com",
           "redhat-translation@bengalinux.org", ),
    "bn_IN": ("anubad@lists.ankur.org.in", ),
    "br": ("drouizig@drouizig.org", "brenux@free.fr",
           "tradgnome@softcatala.net", "fedora@softcatala.org", ),
    "bs": ("lokal@linux.org.ba", "lokal@lugbih.org", ),
    "ca": ("@softcatala.org",),
    "crh": ("tilde-birlik-tercime@lists.sourceforge.net", ),
    "cs": ("fedora-cs-list@redhat.com", "cs-users@lists.fedoraproject.org",
           "debian-l10n-czech@lists.debian.org",
           "kde-czech-apps@lists.sourceforge.net",
           "kde-czech-apps@lists.sf.net", "translations.cs@gnupg.cz"),
    "cy": ("gnome-cy@lists.linux.org.uk", "gnome-cy@pengwyn.linux.org.uk",
           "gnome-cy@www.linux.org", "gnome-cy@www.linux.org.uk",
           "cy@pengwyn.linux.org.uk", ),
    "da": ("dansk@dansk-gruppen.dk", "dansk@klid.dk",
           "sslug-locale@sslug.dk", ),
    "de": ("gnome-de@gnome.org", "debian-l10n-german@lists.debian.org", ),
    "dz": ("pgeyleg@dit.gov.bt", "pgyeleg@dit.gov.bt", ),
    "el": ("debian-l10n-greek@lists.debian.org", "i18ngr@lists.hellug.gr",
           "i18n@hellug.gr", "nls@tux.hellug.gr", "team@gnome.gr",
           "team@lists.gnome.gr", "users@el.openoffice.org", ),
    "en_AU": ("trans@six-by-nine.com.au", ),
    "en_CA": ("adamw@gnome.org", "adamw@freebsd.org", ),
    "en_GB": ("kde-en-gb@kde.me.uk", ),
    "en@shaw": ("ubuntu-l10n-en-shaw@launchpad.net",
                "ubuntu-l10n-en-shaw@lists.launchpad.net", ),
    "eo": ("eo-tradukado@lists.tuxfamily.org",
           "debian-l10n-esperanto@lists.debian.org",
           "ubuntu-l10n-eo@lists.launchpad.net",
           "eo-tradukado.tuxfamily.org", ),
    "es": ("pgsql-es-ayuda@postgresql.org",
           "debian-l10n-spanish@lists.debian.org",
           "gnome-es@gnome.org", "traductores@es.gnome.org", ),
    "et": ("gnome-et@linux.ee", "kde-et@linux.ee", "linux-ee@lists.eenet.ee",
           "linux-et@lists.eenet.ee", "et-gnome@linux.ee",
           "linux-ee@eenet.ee", ),
    "eu": ("debian-l10n-basque@lists.debian.org",
           "debian-l10n-eu@lists.debian.org", "itzulpena@euskalgnu.org",
           "gnome@euskalgnu.org", "librezale@librezale.org",
           "linux-eu@chanae.alphanet.ch", ),
    "fa": ("farsi@lists.sharif.edu", "Farsiweb.info", ),
    "fi": ("debian-l10n-finnish@lists.debian.org",
           "gnome-fi-laatu@lists.sourceforge.net", "laatu@lokalisointi.org",
           "lokalisointi-laatu@linux-aktivaattori.org", "laatu@gnome.fi",
           "yast-trans-fi@kotoistaminen.novell.fi", ),
    "fr": ("debian-l10n-french@lists.debian.org", "gnomefr@traduc.org",
           "kde-francophone@kde.org", "traduc@traduc.org",
           "pgsql-fr-generale@postgresql.org", "rpm-fr@livna.org", ),
    "ga": ("gaeilge-gnulinux@lists.sourceforge.net",
           "gaeilge-a@listserv.heanet.ie", ),
    "gl": ("trasno@ceu.fi.udc.es", "gnome@g11n.net",
           "gpul-traduccion@ceu.fi.udc.es", "proxecto@trasno.net",
           "trasno@gpul.org", ),
    "gu": ("indianoss-gujarati@lists.sourceforge.net", ),
    "he": ("debian-hebrew-common@lists.alioth.debian.org",
           "kde-il@yahoogroups.com", "fedora-he-list@redhat.com",
           "mdk-hebrew@iglu.org.il", ),
    "hi": ("indlinux-hindi-gnome@lists.sourceforge.net",
           "indlinux-hindi@lists.sourceforge.net", ),
    "hr": ("translator-shop.org", "lokalizacija@linux.hr", ),
    "hu": ("debian-l10n-hungarian@lists.debian.org", "gnome@fsf.hu",
           "gnome@gnome.hu", "magyar@lists.linux.hu", ),
    "id": ("@id.gnome.org", "@gnome.linux.or.id", "mdk-id@yahoogroups.com",
           "linux.or.id", "gnome@i15n.org"),
    "io": ("gnome-ido@lists.mterry.name", ),
    "is": ("gnome@techattack.nu", "kde-isl@mmedia.is", "kde-isl@molar.is", ),
    "it": ("debian-l10n-italian@lists.debian.org", "traduzioni@itpug.org",
           "fedora-trans-it@redhat.com", "tp@lists.linux.it", ),
    "ja": ("debian-doc@debian.or.jp", "debian-japanese@lists.debian.org",
           "gnome-translation@gnome.gr.jp", "translation@gnome.gr.jp",
           "jpug-doc@ml.postgresql.jp", ),
    "ka": ("geognome@googlegroups.com",
           "Ubuntu-Georgian-Translators@googlegroups.com", ),
    "kk": ("kk_KZ@googlegroups.com", ),
    "km": ("@khmeros.info", ),
    "kn": ("debian-l10n-kannada@lists.debian.org", ),
    "ko": ("gnome-kr-hackers@list.kldp.net", "gnome-kr-hackers@lists.kldp.net",
           "gnome-kr-translation@lists.kldp.net", "pgsql-kr@postgresql.or.kr",
           "hangul-hackers@lists.kldp.net",
           "debian-l10n-korean@lists.debian.org",
           "gnome-kr-translation@lists.sourceforge.net", ),
    "ks": ("ks-gnome-trans-commits@lists.code.indlinux.net", ),
    "ku": ("gnu-ku-wergerandin@lists.sourceforge.net", ),
    "ky": ("i18n-team-ky-kyrgyz@lists.sourceforge.net", "ky-li@mail.ru", ),
    "la": ("gnome-latin-list@gnome.org", ),
    "li": ("li@gnome.org", ),
    "lt": ("gimp-lt@lists.akl.lt", "gnome-lt@lists.akl.lt",
           "gnome-lt@lists.gnome.org", "komp_lt@konferencijos.lt", ),
    "lv": ("lata-l10n@googlegroups.com", "lata-i18n@groups.google.com",
           "locale@laka.lv", "ll10nt@os.lv", ),
    "mai": ("maithili.sf.net", ),
    "mg": ("i18n-malagasy-gnome@gnome.org", ),
    "mi": ("maori@nzlinux.org.nz", ),
    "mk": ("gnomk-main@lists.sourceforge.net", "lug@lists.linux.net.mk",
           "mkde-l10n@lists.sourceforge.net",
           "ossm-members@hedona.on.net.mk", ),
    "ml": ("smc-discuss@googlegroups.com", ),
    "mn": ("openmn-", "openmn.org", ),
    "ms": ("gabai-penyumbang@lists.sourceforge.net",
           "gabai-penyumbang@lists.sf.net", "kedidiemas@yahoogroups.com", ),
    "nb": ("i18n-nb@lister.ping.uio.no", ),
    "nds": ("nds-lowgerman@lists.sourceforge.net", ),
    "ne": ("info@mpp.org.np", ),
    "nl": ("debian-l10n-dutch@lists.debian.org", "vertaling@nl.gnome.org",
           "vertaling@vrijschrift.org", "nl@vrijschrift.org",
           "vertaling@nl.linux.org", "vertaling@nl.li.org", ),
    "nn": ("i18n-nn@lister.ping.uio.no", ),
    "nso": ("sepedi@translate.org.za", ),
    "or": ("oriya-group@lists.sarovar.org", "oriya-it@googlegroups.com", ),
    "pa": ("punjabi-l10n@users.sf.net", "fedora-pa-list@redhat.com",
           "punjabi-users@lists.sf.net", "punjabi-l10n@lists.sourceforge.net",
           "punlinux-i18n@lists.sourceforge.net", ),
    "pl": ("gnomepl@aviary.pl", "debian-l10n-polish@lists.debian.org",
           "gnome-l10n@lists.aviary.pl", "translators@gnomepl.org", ),
    "ps": ("pathanisation@googelgroups.com", ),
    "pt": ("fedora-trans-pt@redhat.org", "gnome_pt@yahoogroups.com",
           "traduz@debianpt.org", "traduz@debian.pt", ),
    "pt_BR": ("gnome-l10n-br@listas.cipsga.org.br",
              "gnome-pt_br-list@gnome.org", "fedora-docs-br@redhat.com",
              "fedora-trans-pt-br@redhat.com", "ldp-br@bazar.conectiva.com.br",
              "pgbr-dev@postgresql.org.br",
              "pgbr-dev@listas.postgresql.org.br",
              "debian-l10n-portuguese@lists.debian.org", ),
    "ro": ("fedora-ro@googlegroups.com", "gnomero-list@lists.sourceforge.net",
           "debian-l10n-romanian@lists.debian.org", ),
    "ru": ("pgsql-rus@yahoogroups.com", "debian-l10n-russian@lists.debian.org",
           "gnupg-ru@gnupg.org", ),
    "sk": ("sk-i18n@lists.linux.sk", "kde-sk@linux.sk", ),
    "sl": ("gnome-si@googlegroups.com", ),
    "sq": ("gnome-albanian-perkthyesit@lists.sourceforge.net",
           "debian-l10n-albanian@lists.debian.org", ),
    "sr": ("@prevod.org", "serbiangnome-lista@nongnu.org", ),
    "sv": ("debian-l10n-swedish@lists.debian.org", "tp-sv@listor.tp-sv.se", ),
    "ta": ("gnome-tamil-translation@googlegroups.com",
           "tamilinix@yahoogroups.com", "Ubuntu-l10n-tam@lists.ubuntu.com",
           "tamil-DI@yahoogroups.com", ),
    "te": ("localisation@swecha.org",
           "indlinux-telugu@lists.sourceforge.net", ),
    "th": ("l10n@opentle.org", "thai-l10n@googlegroup.com",
           "thailang@buraphalinux.org", "thai-l10n@googlegroups.com",
           "l10n.opentle.org", ),
    "tk": ("kakilikgroup@yahoo.com", ),
    "tl": ("debian-tl@banwa.upm.edu.ph", ),
    "tr": ("debian-l10n-turkish@lists.debian.org", "gnome-turk@gnome.org",
           "gnu-tr-u12a@lists.sourceforge.net", "turkce@pardus.org.tr", ),
    "tt": ("tatarish.l10n@gmail.com", ),
    "ug": ("gnome-uighur@yahoogroups.com", ),
    "uk": ("linux@linux.org.ua", ),
    "ur": ("l10n@urduweb.org", "urdu.scs.gift@gmail.com", ),
    "ve": ("venda@translate.org.za", ),
    "vi": ("gnomevi-list@lists.sourceforge.net", "vi-VN@googlegroups.com", ),
    "wa": ("linux-wa@", ),
    "xh": ("xh-translate@ubuntu.com", "xhosa@translate.org.za",
           "xhosa@ubuntu.com", ),
    "zh_CN": ("i18n-translation@lists.linux.net.cn",
              "i18n-zh@googlegroups.com",
              "translation-team-zh-cn@lists.sourceforge.net",
              "i18n-zh@googlegroup.com", ),
    "zh_TW": ("zh-l10n@lists.linux.org.tw", "chinese-l10n@googlegroups.com",
              "community@linuxhall.org", "zh-l10n@linux.org.tw", ),
    "zu": ("zulu@translate.org.za", ),
}
"""Language codes with snippets of contact information that can be used to
uniquely identify the language"""

LANG_TEAM_LANGUAGE_SNIPPETS = {
    "af": ("Afrikaans",),
    "am": ("Amharic",),
    "ang": ("Old English",),
    "ar": ("Arabic", ),
    "as": ("Assamese", ),
    "ast": ("Asturian", ),
    "az": ("Azerbaijani", u"Azərbaycan", ),
    "bg": ("Bulgarian", ),
    "be@latin": ("Belarusian Latin", ),
    "be": ("Belarusian", "Belorussian", ),
    "bn_IN": ("Bengali (India)", "Bengali INDIA", "Bengali India", ),
    "bn": ("Bangladeshi", "Bengali", ),
    "br": ("Breton", "Britton", ),
    "bs": ("Bosanski", "Bosnian", ),
    "byn": ("Blin", ),
    "ca": ("Catalan", ),
    "ckb": ("Kurdish (Sorani)", ),
    "crh": ("Crimean Tatar", "Crimean Turkish", ),
    "cs": ("Czech", ),
    "cy": ("Cymru", "Welsh", ),
    "da": ("Danish", "Dansk", ),
    "de": ("Deutsch", "German", ),
    "dz": ("Dzongkha", ),
    "el": ("Greek", ),
    "en_GB": ("British English", "en_GB", "English (Great Britain)", ),
    "eo": ("Esperanto", ),
    "es": ("Spanish", "es_ES", u"Español", ),
    "et": ("Eesti", "Estonian", ),
    "eu": ("Basque", "Euskara", ),
    "fa": ("Persian", ),
    "fi": ("Finnish", "Suomi", ),
    "fo": ("Faroese", ),
    "fr": ("French", u"Français", ),
    "fur": ("Friulian", ),
    "ga": ("Irish", ),
    "gez": ("Geez", ),
    "gl": ("Galego", "Galician", "Gallegan", "gl_ES", ),
    "gu": ("Gujarati", ),
    "haw": ("Hawaiian", ),
    "he": ("Hebrew", ),
    "hi": ("Hindi", ),
    "hr": ("Croatian", ),
    "hu": ("Hungarian", ),
    "hy": ("Armenian", ),
    "ia": ("Interlingua", ),
    "id": ("Bahasa Indonesia", "Indonesia", "Indonesian", ),
    "ig": ("Igbo", ),
    "is": ("Icelandic", ),
    "it": ("Italian", ),
    "ja": ("Japanese", ),
    "ka": ("Georgian", ),
    "kk": ("Kazakh", ),
    "km": ("Khmer", ),
    "kn": ("Kannada", ),
    "ko": ("Korean", "Hangul", ),
    "kok": ("Konkani", ),
    "ks": ("Kashmiri", ),
    "ku": ("Kurdish", ),
    "ky": ("Kitghiz", "Kirghiz", ),
    "lg": ("Luganda", ),
    "li": ("Limburgish", ),
    "lt": ("Lithuanian", ),
    "lv": ("Latvian", "lv_LV", "Valoda", u"Latviešu", ),
    "mal": ("Malayalam", ),
    "mg": ("Malagasy", ),
    "mi": ("Maori", ),
    "mk": ("Macedonian", ),
    "ml": ("Malayalam", ),
    "mn": ("Mongolian", ),
    "mt": ("Marathi", ),
    "ms": ("Malay", "Bahasa Melayu", ),
    "my": ("Burmese", ),
    "nb": ("Norwegian Bokmaal", u"Norsk bokmål", u"Norwegian Bokmål",
           u"Norwegian bokmål", ),
    "nds": ("Low Saxon", ),
    "nl": ("Dutch", "Nederlands", ),
    "nn": ("Norwegian nynorsk", "Nynorsk", ),
    "oc": ("Occitan", ),
    "or": ("Oriya", ),
    "pa": ("Punjabi", "Panjabi", ),
    "pl": ("Polish", ),
    "ps": ("Pashto", "Pushto", ),
    "pt_BR": ("Brazilian Portuguese", u"Português/Brasil",
              u"Português do Brasil", ),
    "pt": ("Portuguese", ),
    "rm": ("Rhaeto-Romance", ),
    "ro": ("Romania", "Romanian", u"Română", ),
    "ru": ("Russian", ),
    "si": ("Sinhala", "Sinhalese", ),
    "sk": ("Slovak", ),
    "sl": ("Slovene", "Slovenian", ),
    "so": ("Somali", ),
    "sq": ("Albanian", ),
    "sr": ("Serbian", ),
    "sv": ("Swedish", ),
    "sw": ("Swahili", ),
    "ta": ("Tamil", ),
    "te": ("Telugu", ),
    "tet": ("Tetum", ),
    "tg": ("Tajik", ),
    "th": ("Thai", ),
    "ti": ("Tigrinya", ),
    "tig": ("Tigre", ),
    "tl": ("Tagalog", ),
    "tr": ("Turkish", u"Türkçe", u"Türkiye", ),
    "tt": ("Tatarish", ),
    "ug": ("Uighur", ),
    "uk": ("Ukrainian", ),
    "ur": ("Urdu", ),
    "uz": ("Uzbek", ),
    "ve": ("Venda", u"Tshivenḓa", "Tshivenda", ),
    "vi": ("Vietnamese", ),
    "wa": ("Walloon", ),
    "wal": ("Walamo", ),
    "wo": ("Wolof", ),
    "xh": ("Xhosa", "IsiXhosa", "isiXhosa", ),
    "yi": ("Yiddish", ),
    "yo": ("Yoruba", ),
    "zh_CN": ("Chinese Simplified", "Chinese/Simplified",
              "Chinese (simplified)", "Simplified Chinese", ),
    "zh_HK": ("Chinese (Hong Kong)", ),
    "zh_TW": ("Chinese (traditional)", "Chinese/Traditional",
              "Traditional Chinese", ),
}
"""Language codes with snippets of language names, including English, native
spelling and varients, that can be used to uniquely identify the language"""


def _regex_guesser(prefilter, regex, string, postfilter=None):
    """Use regular expressions to extract the language team

    :param prefilter: simple filter to apply before attempting the regex
    :param regex: regular expression with one group that will contain
    the language code
    :param string: the language team string that should be examined
    :param postfilter: filter to apply to reject any potential matches
    after they have been retreived by the regex
    :return: ISO language code for the found language
    """
    # TODO instead of a posfilter, have a dictionary of transform rules
    # e.g. for debian-l10n-albanian a dict of {'russian': 'ru' would allow
    # transformation.  {'default': None} would ensure that anything we
    # don't understand gets ignored.  Or {'default': 'nothing'} means to
    # nothing.
    if prefilter in string:
        found = re.search(regex, string)
        if found:
            regex_lang = found.groups()[0]
        else:
            return None
        if postfilter is not None and regex_lang in postfilter:
            return None
        if regex_lang and regex_lang != 'en':
            return regex_lang
    return None


def _nofilter(text):
    """Return the supplied text unchanged"""
    return text


def _lower(text):
    """Convert the supplied text to lowercase"""
    return text.lower()


def _snippet_guesser(snippets_dict, string, filter_=_nofilter):
    """Guess the language based on a snippet of text in the language team
    string.

    :param snippets_dict: A dict of snippets that can be used to identify a
    language in the format {'lang': ('snippet1', 'snippet2'), 'lang2'...}
    :param string: The language string to be analysed
    :param filter_: a function to be applied to the string and snippets
    before examination
    """
    string = filter_(string)
    for possible_lang, snippets in snippets_dict.iteritems():
        for snippet in snippets:
            if filter_(snippet) in string:
                return possible_lang
    return None


def guess_language(team_string):
    """Gueses the language of a PO file based on the Language-Team entry"""

    for prefilter, regex, postfilter in LANG_TEAM_REGEX:
        lang = _regex_guesser(prefilter, regex, team_string, postfilter)
        if lang:
            break

    if not lang:
        lang = _snippet_guesser(LANG_TEAM_CONTACT_SNIPPETS, team_string,
                                _lower)

    if not lang:
        lang = _snippet_guesser(LANG_TEAM_LANGUAGE_SNIPPETS, team_string)

    # TODO Maybe clean everything and see of we have a language code only

    if not lang:
        #print (u"MISSED: '%s'" % team_string).encode('utf-8')
        return None
    return lang

if __name__ == "__main__":
    from sys import argv
    from translate.storage import factory
    for fname in argv[1:]:
        store = factory.getobject(fname)
        print(fname, guess_language(store.parseheader().get('Language-Team', u"")))
