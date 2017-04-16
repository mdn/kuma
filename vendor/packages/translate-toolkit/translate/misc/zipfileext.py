#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2004, 2005 Zuza Software Foundation
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

"""extensions to zipfile standard module that will hopefully get included in future..."""

from zipfile import ZipFile, struct, structCentralDir, stringCentralDir, structEndArchive, stringEndArchive

class ZipFileExt(ZipFile, object):
    """a ZipFile that can handle replacing objects"""
    def delete(self, name):
        """Delete the file from the archive. If it appears multiple
        times only the first instance will be deleted."""
        for i in range (0, len(self.filelist)):
            if self.filelist[i].filename == name:
                if self.debug:
                    print "Removing", name
                deleted_offset = self.filelist[i].header_offset
                # "file_offset" is only available in python up to 2.4
                if hasattr(self.filelist[i], "file_offset"):
                    deleted_size   = (self.filelist[i].file_offset - self.filelist[i].header_offset) + self.filelist[i].compress_size
                else:
                    deleted_size   = (len(self.filelist[i].FileHeader()) - self.filelist[i].header_offset) + self.filelist[i].compress_size
                zinfo_size = struct.calcsize(structCentralDir) + len(self.filelist[i].filename) + len(self.filelist[i].extra)
                # Remove the file's data from the archive.
                current_offset = self.fp.tell()
                # go to the end of the archive to calculate the total archive_size
                self.fp.seek(0, 2)
                archive_size = self.fp.tell()
                self.fp.seek(deleted_offset + deleted_size)
                buf = self.fp.read()
                self.fp.seek(deleted_offset)
                self.fp.write(buf)
                self.fp.truncate(archive_size - deleted_size - zinfo_size)
                # go to the end of the archive to calculate the total archive_size
                self.fp.seek(0, 2)
                if self.debug >= 2:
                    if self.fp.tell() != archive_size - deleted_size - zinfo_size:
                        print "truncation failed: %r != %r" % (self.fp.tell(), archive_size - deleted_size - zinfo_size)
                if current_offset > deleted_offset + deleted_size:
                    current_offset -= deleted_size
                elif current_offset > deleted_offset:
                    current_offset = deleted_offset
                self.fp.seek(current_offset, 0)
                # Remove file from central directory.
                del self.filelist[i]
                # Adjust the remaining offsets in the central directory.
                for j in range (i, len(self.filelist)):
                    if self.filelist[j].header_offset > deleted_offset:
                        self.filelist[j].header_offset -= deleted_size
                    # "file_offset" is only available in python up to 2.4
                    if hasattr(self.filelist[i], "file_offset"):
                        if self.filelist[j].file_offset > deleted_offset:
                            self.filelist[j].file_offset -= deleted_size
                del self.NameToInfo[name]
                return
        if self.debug:
            print name, "not in archive"

    def close(self):
        """Close the file, and for mode "w" and "a" write the ending
        records."""
        if self.fp is None:
            return
        self.writeendrec()
        if not self._filePassed:
            self.fp.close()
        self.fp = None

    def writeendrec(self):
        """Write the ending records (without neccessarily closing the file)"""
        if self.mode in ("w", "a"):             # write ending records
            count = 0
            current_offset = self.fp.tell()
            pos1 = self.fp.tell()
            for zinfo in self.filelist:         # write central directory
                count = count + 1
                dt = zinfo.date_time
                dosdate = (dt[0] - 1980) << 9 | dt[1] << 5 | dt[2]
                dostime = dt[3] << 11 | dt[4] << 5 | (dt[5] // 2)
                centdir = struct.pack(structCentralDir,
                  stringCentralDir, zinfo.create_version,
                  zinfo.create_system, zinfo.extract_version, zinfo.reserved,
                  zinfo.flag_bits, zinfo.compress_type, dostime, dosdate,
                  zinfo.CRC, zinfo.compress_size, zinfo.file_size,
                  len(zinfo.filename), len(zinfo.extra), len(zinfo.comment),
                  0, zinfo.internal_attr, zinfo.external_attr,
                  zinfo.header_offset)
                self.fp.write(centdir)
                self.fp.write(zinfo.filename)
                self.fp.write(zinfo.extra)
                self.fp.write(zinfo.comment)
            pos2 = self.fp.tell()
            # Write end-of-zip-archive record
            endrec = struct.pack(structEndArchive, stringEndArchive,
                     0, 0, count, count, pos2 - pos1, pos1, 0)
            self.fp.write(endrec)
            self.fp.seek(pos1)

