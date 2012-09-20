from django.contrib.sitemaps import Sitemap
from wiki.models import (Document, Revision)

class DocumentSitemap(Sitemap):
	changefreq = 'weekly'
	priority = 0.5
	
	def items(self):
		docs = Document.objects.filter(is_template=False)
		return docs

	def lastmod(self, doc):
		return doc.current_revision.created

	def location(self, doc):
		return doc.get_absolute_url()