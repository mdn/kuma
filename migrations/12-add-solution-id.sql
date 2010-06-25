ALTER TABLE `questions_question` ADD `solution_id` integer;
ALTER TABLE `questions_question` ADD CONSTRAINT `solution_id_refs_id_95fb9a4d` FOREIGN KEY (`solution_id`) REFERENCES `questions_answer` (`id`);
