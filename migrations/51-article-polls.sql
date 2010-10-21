CREATE TABLE `wiki_helpfulvote` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `document_id` integer NOT NULL,
    `helpful` bool NOT NULL,
    `created` datetime NOT NULL,
    `creator_id` integer,
    `anonymous_id` varchar(40) NOT NULL,
    `user_agent` varchar(1000) NOT NULL
);
ALTER TABLE `wiki_helpfulvote` ADD CONSTRAINT `document_id_refs_id_1ab69a8f` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`);
ALTER TABLE `wiki_helpfulvote` ADD CONSTRAINT `creator_id_refs_id_b1375de5` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);

CREATE INDEX `wiki_helpfulvote_f4226d13` ON `wiki_helpfulvote` (`document_id`);
CREATE INDEX `wiki_helpfulvote_3216ff68` ON `wiki_helpfulvote` (`created`);
CREATE INDEX `wiki_helpfulvote_f97a5119` ON `wiki_helpfulvote` (`creator_id`);
CREATE INDEX `wiki_helpfulvote_2291b592` ON `wiki_helpfulvote` (`anonymous_id`);
