# -*- coding: utf-8 -*-

from translate.storage.placeables import general


def test_placeable_numbers():
    """Check the correct functioning of number placeables"""
    assert general.NumberPlaceable([u"25"]) in general.NumberPlaceable.parse(u"Here is a 25 number")
    assert general.NumberPlaceable([u"-25"]) in general.NumberPlaceable.parse(u"Here is a -25 number")
    assert general.NumberPlaceable([u"+25"]) in general.NumberPlaceable.parse(u"Here is a +25 number")
    assert general.NumberPlaceable([u"25.00"]) in general.NumberPlaceable.parse(u"Here is a 25.00 number")
    assert general.NumberPlaceable([u"2,500.00"]) in general.NumberPlaceable.parse(u"Here is a 2,500.00 number")
    assert general.NumberPlaceable([u"1\u00a0000,99"]) in general.NumberPlaceable.parse(u"Here is a 1\u00a0000,99 number")


def test_placeable_newline():
    assert general.NewlinePlaceable.parse(u"A newline\n")[1] == general.NewlinePlaceable([u"\n"])
    assert general.NewlinePlaceable.parse(u"First\nSecond")[1] == general.NewlinePlaceable([u"\n"])


def test_placeable_alt_attr():
    assert general.AltAttrPlaceable.parse(u'Click on the <img src="image.jpg" alt="Image">')[1] == general.AltAttrPlaceable([u'alt="Image"'])


def test_placeable_qt_formatting():
    assert general.QtFormattingPlaceable.parse(u'One %1 %99 %L1 are all valid')[1] == general.QtFormattingPlaceable([u'%1'])
    assert general.QtFormattingPlaceable.parse(u'One %1 %99 %L1 are all valid')[3] == general.QtFormattingPlaceable([u'%99'])
    assert general.QtFormattingPlaceable.parse(u'One %1 %99 %L1 are all valid')[5] == general.QtFormattingPlaceable([u'%L1'])


def test_placeable_camelcase():
    assert general.CamelCasePlaceable.parse(u'CamelCase')[0] == general.CamelCasePlaceable([u'CamelCase'])
    assert general.CamelCasePlaceable.parse(u'iPod')[0] == general.CamelCasePlaceable([u'iPod'])
    assert general.CamelCasePlaceable.parse(u'DokuWiki')[0] == general.CamelCasePlaceable([u'DokuWiki'])
    assert general.CamelCasePlaceable.parse(u'KBabel')[0] == general.CamelCasePlaceable([u'KBabel'])
    assert general.CamelCasePlaceable.parse(u'_Bug') is None
    assert general.CamelCasePlaceable.parse(u'NOTCAMEL') is None


def test_placeable_space():
    assert general.SpacesPlaceable.parse(u' Space at start')[0] == general.SpacesPlaceable([u' '])
    assert general.SpacesPlaceable.parse(u'Space at end ')[1] == general.SpacesPlaceable([u' '])
    assert general.SpacesPlaceable.parse(u'Double  space')[1] == general.SpacesPlaceable([u'  '])


def test_placeable_punctuation():
    assert general.PunctuationPlaceable.parse(u'These, are not. Special: punctuation; marks! Or are "they"?') is None
    assert general.PunctuationPlaceable.parse(u'Downloading…')[1] == general.PunctuationPlaceable([u'…'])


def test_placeable_xml_entity():
    assert general.XMLEntityPlaceable.parse(u'&brandShortName;')[0] == general.XMLEntityPlaceable([u'&brandShortName;'])
    assert general.XMLEntityPlaceable.parse(u'&#1234;')[0] == general.XMLEntityPlaceable([u'&#1234;'])
    assert general.XMLEntityPlaceable.parse(u'&xDEAD;')[0] == general.XMLEntityPlaceable([u'&xDEAD;'])


def test_placeable_xml_tag():
    assert general.XMLTagPlaceable.parse(u'<a>koei</a>')[0] == general.XMLTagPlaceable([u'<a>'])
    assert general.XMLTagPlaceable.parse(u'<a>koei</a>')[2] == general.XMLTagPlaceable([u'</a>'])
    assert general.XMLTagPlaceable.parse(u'<Exif.XResolution>')[0] == general.XMLTagPlaceable([u'<Exif.XResolution>'])
    assert general.XMLTagPlaceable.parse(u'<tag_a>')[0] == general.XMLTagPlaceable([u'<tag_a>'])
    assert general.XMLTagPlaceable.parse(u'<img src="koei.jpg" />')[0] == general.XMLTagPlaceable([u'<img src="koei.jpg" />'])
    # We don't want this to be recognised, so we test for None - not sure if that is a stable assumption
    assert general.XMLTagPlaceable.parse(u'<important word>') is None
    assert general.XMLTagPlaceable.parse(u'<img ="koei.jpg" />') is None
    assert general.XMLTagPlaceable.parse(u'<img "koei.jpg" />') is None
    assert general.XMLTagPlaceable.parse(u'<span xml:space="preserve">')[0] == general.XMLTagPlaceable([u'<span xml:space="preserve">'])
    assert general.XMLTagPlaceable.parse(u'<img src="http://translate.org.za/blogs/friedel/sites/translate.org.za.blogs.friedel/files/virtaal-7f_help.png" alt="Virtaal met lêernaam-pseudovertaling" style="border: 1px dotted grey;" />')[0] == general.XMLTagPlaceable([u'<img src="http://translate.org.za/blogs/friedel/sites/translate.org.za.blogs.friedel/files/virtaal-7f_help.png" alt="Virtaal met lêernaam-pseudovertaling" style="border: 1px dotted grey;" />'])
    # Bug 933
    assert general.XMLTagPlaceable.parse(u'This entry expires in %days% days. Would you like to <a href="%href%?PHPSESSID=5d59c559cf4eb9f1d278918271fbe68a" title="Renew this Entry Now">Renew this Entry Now</a> ?')[1] == general.XMLTagPlaceable([u'<a href="%href%?PHPSESSID=5d59c559cf4eb9f1d278918271fbe68a" title="Renew this Entry Now">'])
    assert general.XMLTagPlaceable.parse(u'''<span weight='bold' size='larger'>Your Google Account is locked</span>''')[0] == general.XMLTagPlaceable([u'''<span weight='bold' size='larger'>'''])


def test_placeable_option():
    assert general.OptionPlaceable.parse(u'Type --help for this help')[1] == general.OptionPlaceable([u'--help'])
    assert general.OptionPlaceable.parse(u'Short -S ones also')[1] == general.OptionPlaceable([u'-S'])


def test_placeable_file():
    assert general.FilePlaceable.parse(u'Store in /home/user')[1] == general.FilePlaceable([u'/home/user'])
    assert general.FilePlaceable.parse(u'Store in ~/Download directory')[1] == general.FilePlaceable([u'~/Download'])


def test_placeable_email():
    assert general.EmailPlaceable.parse(u'Send email to info@example.com')[1] == general.EmailPlaceable([u'info@example.com'])
    assert general.EmailPlaceable.parse(u'Send email to mailto:info@example.com')[1] == general.EmailPlaceable([u'mailto:info@example.com'])


def test_placeable_caps():
    assert general.CapsPlaceable.parse(u'Use the HTML page')[1] == general.CapsPlaceable([u'HTML'])
    assert general.CapsPlaceable.parse(u'I am') is None
    assert general.CapsPlaceable.parse(u'Use the A4 paper') is None
    assert general.CapsPlaceable.parse(u'In GTK+')[1] == general.CapsPlaceable([u'GTK+'])
#    assert general.CapsPlaceable.parse(u'GNOME-stuff')[0] == general.CapsPlaceable([u'GNOME'])
    assert general.CapsPlaceable.parse(u'with XDG_USER_DIRS')[1] == general.CapsPlaceable([u'XDG_USER_DIRS'])


def test_placeable_formatting():
    fp = general.FormattingPlaceable
    assert fp.parse(u'There were %d cows')[1] == fp([u'%d'])
    assert fp.parse(u'There were %Id cows')[1] == fp([u'%Id'])
    assert fp.parse(u'There were %d %s')[3] == fp([u'%s'])
    assert fp.parse(u'%1$s was kicked by %2$s')[0] == fp([u'%1$s'])
    assert fp.parse(u'There were %Id cows')[1] == fp([u'%Id'])
    assert fp.parse(u'There were % d cows')[1] == fp([u'% d'])
    # only a real space is allowed as formatting flag
    assert fp.parse(u'There were %\u00a0d cows') is None
    assert fp.parse(u"There were %'f cows")[1] == fp([u"%'f"])
    assert fp.parse(u"There were %#x cows")[1] == fp([u"%#x"])

    # field width
    assert fp.parse(u'There were %3d cows')[1] == fp([u'%3d'])
    assert fp.parse(u'There were %33d cows')[1] == fp([u'%33d'])
    assert fp.parse(u'There were %*d cows')[1] == fp([u'%*d'])

    # numbered variables
    assert fp.parse(u'There were %1$d cows')[1] == fp([u'%1$d'])


# TODO: PythonFormattingPlaceable, JavaMessageFormatPlaceable, UrlPlaceable, XMLTagPlaceable
