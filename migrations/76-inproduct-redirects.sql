CREATE TABLE `inproduct_redirect` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `product` varchar(30) NOT NULL,
    `version` varchar(30) NOT NULL,
    `platform` varchar(30) NOT NULL,
    `locale` varchar(10) NOT NULL,
    `topic` varchar(50) NOT NULL,
    `target` varchar(100) NOT NULL,
    UNIQUE (`product`, `version`, `platform`, `locale`, `topic`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_unicode_ci;

CREATE INDEX `inproduct_redirect_81e0dea9` ON `inproduct_redirect` (`product`);
CREATE INDEX `inproduct_redirect_659105e4` ON `inproduct_redirect` (`version`);
CREATE INDEX `inproduct_redirect_eab31616` ON `inproduct_redirect` (`platform`);
CREATE INDEX `inproduct_redirect_928541cb` ON `inproduct_redirect` (`locale`);
CREATE INDEX `inproduct_redirect_277e394d` ON `inproduct_redirect` (`topic`);
