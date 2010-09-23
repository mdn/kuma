BEGIN;
CREATE TABLE `customercare_cannedcategory` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(255) NOT NULL,
    `weight` integer NOT NULL
)
;
CREATE TABLE `customercare_cannedresponse` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(255) NOT NULL,
    `response` varchar(140) NOT NULL
)
;
CREATE TABLE `customercare_categorymembership` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `category_id` integer NOT NULL,
    `response_id` integer NOT NULL,
    `weight` integer NOT NULL
)
;
ALTER TABLE `customercare_categorymembership` ADD CONSTRAINT `category_id_refs_id_e187a5e8` FOREIGN KEY (`category_id`) REFERENCES `customercare_cannedcategory` (`id`);
ALTER TABLE `customercare_categorymembership` ADD CONSTRAINT `response_id_refs_id_8f9177e9` FOREIGN KEY (`response_id`) REFERENCES `customercare_cannedresponse` (`id`);
CREATE INDEX `customercare_cannedcategory_f8f0a775` ON `customercare_cannedcategory` (`weight`);
CREATE INDEX `customercare_categorymembership_42dc49bc` ON `customercare_categorymembership` (`category_id`);
CREATE INDEX `customercare_categorymembership_d5ea739f` ON `customercare_categorymembership` (`response_id`);
CREATE INDEX `customercare_categorymembership_f8f0a775` ON `customercare_categorymembership` (`weight`);
COMMIT;
