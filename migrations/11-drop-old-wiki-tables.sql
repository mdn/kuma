--
-- Since bug 702988 merged master & mdn branches, we should nuke all the old
-- mdn branch wiki tables and start over.
--
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS
    wiki_document,
    wiki_editortoolbar,
    wiki_firefoxversion,
    wiki_helpfulvote,
    wiki_operatingsystem,
    wiki_relateddocument,
    wiki_reviewtag,
    wiki_reviewtaggedrevision,
    wiki_revision;

DELETE FROM south_migrationhistory 
    WHERE app_name="wiki";
