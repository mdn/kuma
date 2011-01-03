CREATE TABLE `dashboards_wikidocumentvisits` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `document_id` integer NOT NULL,
    `visits` integer NOT NULL,
    `period` integer NOT NULL,
    UNIQUE (`period`, `document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
ALTER TABLE `dashboards_wikidocumentvisits` ADD CONSTRAINT `document_id_refs_id_814b8dd0` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`);
CREATE INDEX `dashboards_wikidocumentvisits_f4226d13` ON `dashboards_wikidocumentvisits` (`document_id`);
CREATE INDEX `dashboards_wikidocumentvisits_5bfc8463` ON `dashboards_wikidocumentvisits` (`visits`);
