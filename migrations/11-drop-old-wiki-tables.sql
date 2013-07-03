/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

--
-- Since bug 702988 merged master & mdn branches, we should nuke all the old
-- mdn branch wiki tables and start over.
--
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS
    wiki_document,
    wiki_documenttag,
    wiki_editortoolbar,
    wiki_firefoxversion,
    wiki_helpfulvote,
    wiki_operatingsystem,
    wiki_relateddocument,
    wiki_reviewtag,
    wiki_reviewtaggedrevision,
    wiki_revision,
    wiki_taggeddocument;

DELETE FROM south_migrationhistory 
    WHERE app_name="wiki";
