# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

sql_pattern = """\
SET FOREIGN_KEY_CHECKS=0;
ALTER TABLE taggit_tag
  MODIFY name varchar(100)
    CHARACTER SET utf8 COLLATE %(collation)s;
ALTER TABLE wiki_documenttag
  MODIFY name VARCHAR(100)
    CHARACTER SET utf8 COLLATE %(collation)s
    DEFAULT NULL;
ALTER TABLE wiki_localizationtag
  MODIFY name VARCHAR(100)
    CHARACTER SET utf8 COLLATE %(collation)s
    DEFAULT NULL;
ALTER TABLE wiki_reviewtag
  MODIFY name VARCHAR(100)
   CHARACTER SET utf8 COLLATE %(collation)s
   DEFAULT NULL;
SET FOREIGN_KEY_CHECKS=1;
"""

to_utf8_general_ci = sql_pattern % {'collation': 'utf8_general_ci'}
to_utf8_distinct_ci = sql_pattern % {'collation': 'utf8_distinct_ci'}


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0034_utf8_general_ci_tags'),
    ]

    operations = [migrations.RunSQL(to_utf8_general_ci,
                                    to_utf8_distinct_ci)
    ]
