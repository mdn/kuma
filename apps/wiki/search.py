from elasticutils.contrib.django.models import DjangoMappingType, Indexable

from wiki.models import Document



class DocumentType(DjangoMappingType, Indexable):
    @classmethod
    def get_model(cls):
        return Document

    @classmethod
    def extract_document(cls, obj_id, obj=None):
        if obj is None:
            obj = cls.get_model().objects.get(pk=obj_id)

        return {
            'id': obj.id,
            'title': obj.title,
            'slug': obj.slug,
            'locale': obj.locale,
            'content': obj.rendered_html
        }

    @classmethod
    def get_mapping(cls):
        return {
            'id': {'type': 'integer'},
            'title': {'type': 'string'},
            'slug': {'type': 'string'},
            'locale': {'type': 'string', 'index': 'not_analyzed'},
            'content': {'type': 'string', 'analyzer': 'snowball'}
        }
