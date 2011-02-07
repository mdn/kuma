-- Translation revisions that were migrated rather than created in the new
-- system have no based_on IDs, so the dashboard doesn't know where to start
-- looking for [major or minor] changes in the English article.

-- Set the based_on of the first revision of each translation to the first
-- revision of the English if the based_on was NULL.

-- MySQL can't update the same table that it's doing a subselect from, so use a
-- temp table. :-P
CREATE TEMPORARY TABLE min_english_revisions (
    id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    document_id int REFERENCES wiki_document.id,
    revision_id int REFERENCES wiki_revision.id
);

INSERT INTO min_english_revisions (document_id, revision_id) SELECT wiki_document.id, MIN(wiki_revision.id) FROM wiki_revision
INNER JOIN wiki_document ON wiki_document.id=wiki_revision.document_id AND wiki_document.locale='en-US'
GROUP BY wiki_revision.document_id;

UPDATE wiki_revision transrev
INNER JOIN wiki_document transdoc ON transdoc.id=transrev.document_id
INNER JOIN wiki_document engdoc ON engdoc.id=transdoc.parent_id
SET transrev.based_on_id=(
    SELECT revision_id
    FROM min_english_revisions
    WHERE document_id=engdoc.id)
WHERE
transrev.based_on_id IS NULL
AND transdoc.parent_id IS NOT NULL
AND transdoc.locale!='en-US';
-- We actually have 1 English article with a parent!

-- To test, run this before and after. By my reckoning, there should be a bunch
-- beforehand and none afterward.
--
-- SELECT COUNT(*)
-- FROM wiki_revision
-- INNER JOIN wiki_document ON wiki_document.id=wiki_revision.document_id
-- WHERE wiki_document.locale!='en-US'
-- AND wiki_document.parent_id IS NOT NULL
-- AND wiki_revision.based_on_id IS NULL;
