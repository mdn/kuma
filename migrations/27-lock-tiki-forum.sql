UPDATE
    tiki_comments
SET
    type = 'l'
WHERE
    parentId = 0
    AND objectType = 'forum'
    AND object = 6;
