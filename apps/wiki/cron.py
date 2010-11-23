from django.db import connection, transaction

import cronjobs

from wiki import tasks


@cronjobs.register
def calculate_related_documents():
    """Calculates all related documents based on common tags."""

    cursor = connection.cursor()

    cursor.execute('DELETE FROM wiki_relateddocument')
    cursor.execute("""
        INSERT INTO
            wiki_relateddocument (document_id, related_id, in_common)
        SELECT
            t1.object_id,
            t2.object_id,
            COUNT(*) AS common_tags
        FROM
            wiki_document d1 JOIN
            taggit_taggeditem t1 JOIN
            taggit_taggeditem t2 JOIN
            wiki_document d2
        WHERE
            d1.id = t1.object_id AND
            t1.tag_id = t2.tag_id AND
            t1.object_id <> t2.object_id AND
            t1.content_type_id = (
                SELECT
                    id
                FROM
                    django_content_type
                WHERE
                    app_label = 'wiki' AND
                    model = 'document'
                ) AND
            t2.content_type_id = (
                SELECT
                    id
                FROM
                    django_content_type
                WHERE
                    app_label = 'wiki' AND
                    model = 'document'
                ) AND
            d2.id = t2.object_id AND
            d2.locale = d1.locale AND
            d2.category = d1.category AND
            d1.current_revision_id IS NOT NULL AND
            d2.current_revision_id IS NOT NULL
        GROUP BY
            t1.object_id,
            t2.object_id""")
    transaction.commit_unless_managed()


@cronjobs.register
def rebuild_kb():
    tasks.rebuild_kb()
