-- Add an index on wiki_revision.is_approved
CREATE INDEX `wiki_revision_is_approved_idx`
	ON `wiki_revision` (`is_approved`);
