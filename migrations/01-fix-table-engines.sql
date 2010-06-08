BEGIN;

ALTER TABLE django_content_type ENGINE=InnoDB;
ALTER TABLE django_session ENGINE=InnoDB;
ALTER TABLE django_site ENGINE=InnoDB;

ALTER TABLE auth_group ENGINE=InnoDB;
ALTER TABLE auth_group_permissions ENGINE=InnoDB;
ALTER TABLE auth_message ENGINE=InnoDB;
ALTER TABLE auth_permission ENGINE=InnoDB;
ALTER TABLE auth_user ENGINE=InnoDB;
ALTER TABLE auth_user_groups ENGINE=InnoDB;
ALTER TABLE auth_user_user_permissions ENGINE=InnoDB;

ALTER TABLE forums_forum ENGINE=InnoDB;
ALTER TABLE forums_thread ENGINE=InnoDB;
ALTER TABLE forums_post ENGINE=InnoDB;

COMMIT;
