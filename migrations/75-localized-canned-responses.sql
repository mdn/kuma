ALTER TABLE `customercare_cannedcategory`
    ADD `locale` varchar(7) NOT NULL DEFAULT 'en-US';
ALTER TABLE `customercare_cannedresponse`
    ADD `locale` varchar(7) NOT NULL DEFAULT 'en-US';
CREATE INDEX `customercare_cannedcategory_928541cb`
    ON `customercare_cannedcategory` (`locale`);
CREATE INDEX `customercare_cannedresponse_928541cb`
    ON `customercare_cannedresponse` (`locale`);

ALTER TABLE `customercare_cannedcategory`
    ADD UNIQUE (`title`, `locale`);
ALTER TABLE `customercare_cannedresponse`
    ADD UNIQUE (`title`, `locale`);
