# -*- coding: utf-8 -*-

import os.path

from translate.storage.versioncontrol import (get_versioned_object, run_command,
                                              svn)
from translate.storage.versioncontrol.test_helper import HelperTest


class TestSVN(HelperTest):

    def setup_repo_and_checkout(self):
        run_command(["svnadmin", "create", "repo"], cwd=self.path)
        run_command(["svn", "co", "file:///%s/repo" % self.path, "checkout"], cwd=self.path)

    def test_detection(self):
        print(self.co_path)
        o = get_versioned_object(self.co_path)
        assert isinstance(o, svn.svn)
        assert o.location_abs == self.co_path

    def test_add(self):
        o = get_versioned_object(self.co_path)
        self.create_files({
            "test1.txt": "First file\n",
            "test2.txt": "Second file\n",
        })
        file_path = os.path.join(self.co_path, "test1.txt")
        o.add(os.path.join(file_path))
        o = get_versioned_object(file_path)
        assert os.path.samefile(o.location_abs, file_path)

        assert o.getcleanfile() == "First file\n"
