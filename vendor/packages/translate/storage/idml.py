#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Zuza Software Foundation
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
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import zipfile


# Tags to be extracted as placeables (tags that are within translatable texts).
INLINE_ELEMENTS = [
    ('', 'CharacterStyleRange'),
    ('', 'Content'),
#    ('', 'Br'),
]


# Skipping one of these tags doesn't imply nested acceptable tags are not
# extracted.
NO_TRANSLATE_ELEMENTS = [
    ('http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging', 'Story'),

    ('', 'Story'),  # This is a different Story tag than the one above.
    ('', 'StoryPreference'),
    ('', 'InCopyExportOption'),
    #('', 'ParagraphStyleRange'),
    #('', 'CharacterStyleRange'),

    ('', 'MetadataPacketPreference'),

    ('', 'Contents'),  # Don't confuse with Content tag. This tag contains a
    # lot of CDATA we don't want to parse.

    ('', 'Properties'),
    ('', 'Leading'),
    ('', 'AppliedFont'),

    ('', 'TextFrame'),
    ('', 'PathGeometry'),
    ('', 'GeometryPathType'),
    ('', 'PathPointArray'),
    ('', 'PathPointType'),

    ('', 'AnchoredObjectSetting'),
    ('', 'TextFramePreference'),
    ('', 'TextWrapPreference'),
    ('', 'TextWrapOffset'),
    ('', 'ContourOption'),

    ('', 'EPS'),
    ('', 'GraphicBounds'),
    ('', 'Link'),
    ('', 'ClippingPathSettings'),
    ('', 'FrameFittingOption'),

    ('', 'ObjectExportOption'),
    ('', 'AltMetadataProperty'),
    ('', 'ActualMetadataProperty'),


    ('', 'TabList'),
    ('', 'ListItem'),
    ('', 'Alignment'),
    ('', 'AlignmentCharacter'),
    ('', 'Leader'),
    ('', 'Position'),

    ('', 'Rectangle'),
    #('', 'Br'),
]


def open_idml(filename):
    z = zipfile.ZipFile(filename, 'r')
    # Return a dictionary containing all the files inside the Stories
    # subdirectory, being the keys the filenames (for example
    # 'Stories/Story_u49f.xml' and the values the strings for those files.
    return dict((filename, z.read(filename))
                for filename in z.namelist() if filename.startswith('Stories/'))


def copy_idml(input_zip, output_zip, exclusion_list):
    for name in [name for name in input_zip.namelist()
                 if name not in exclusion_list]:
        output_zip.writestr(name, input_zip.read(name))
    return output_zip
