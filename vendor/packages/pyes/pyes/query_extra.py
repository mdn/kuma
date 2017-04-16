#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Alberto Paro'

from query import Query, HighLighter
from utils import clean_string
from pyes.exceptions import InvalidQuery
__all__ = ["NLPQuery"]

AVAILABLE_NLP_OPTIONS = [
                        'use_stopwords',
                        'use_global_stopwords',
                        'use_expand',
                        'use_expansion',
                        'use_synonyms',
                        'hypernym',
                        'antonym' 
                        'hyponym', 
                        'similar',
                        'also_see', 
                        'attribute', 
                        'substance_meronym', 
                        'class_regional', 
                        'frames', 
                        'pertainym', 
                        'entailment', 
                        'part_meronym', 
                        'substance_holonym', 
                        'domain_category', 
                        'member_meronym', 
                        'cause', 
                        'verb_group', 
                        'domain_regional', 
                        'domain_usage', 
                        'part_holonym', 
                        'class_category', 
                        'class_usage', 
                        'participle_of', 
                        'member_holonym', 
                        'hyponym_instance', 
                        'hypernym_instance',
                         ]

class NLPQuery(Query):
    _internal_name = "query_nlp"
    
    def __init__(self, query, language, default_field = None,
                 search_fields = None,
                 synonyms = None,
                stopwords = None,
                default_operator = "OR",
                analyzer = None,
                options = None,
                allow_leading_wildcard = True,
                lowercase_expanded_terms = True,
                enable_position_increments = True,
                fuzzy_prefix_length = 0,
                fuzzy_min_sim = 0.5,
                phrase_slop = 0,
                boost = 1.0,
                use_dis_max = True,
                tie_breaker = 0, 
                min_concept_size = 2,
                max_concept_size = 4,
                term_expansion_steps = 1,
                clean_text=False,
                **kwargs):
        super(NLPQuery, self).__init__(**kwargs)
        self.text = query
        self.search_fields = search_fields
        self.language = language
        self.default_field = default_field
        self.default_operator = default_operator
        self.analyzer = analyzer
        self.allow_leading_wildcard = allow_leading_wildcard
        self.lowercase_expanded_terms = lowercase_expanded_terms
        self.enable_position_increments = enable_position_increments
        self.fuzzy_prefix_length = fuzzy_prefix_length
        self.fuzzy_min_sim = fuzzy_min_sim
        self.phrase_slop = phrase_slop 
        self.boost = boost
        self.use_dis_max = use_dis_max
        self.tie_breaker = tie_breaker
        self.synonyms = synonyms or []
        self.stopwords = stopwords or []
        self.options = options or []
        self.min_concept_size = min_concept_size
        self.max_concept_size = max_concept_size
        self.term_expansion_steps = term_expansion_steps
        self.clean_text=clean_text

    def serialize(self):
        filters = {'language':self.language}
        if self.default_field:
            filters["default_field"] = self.default_field
            if not isinstance(self.default_field, (str, unicode)) and isinstance(self.default_field, list):
                if not self.use_dis_max:
                    filters["use_dis_max"] = self.use_dis_max
                if self.tie_breaker != 0:
                    filters["tie_breaker"] = self.tie_breaker
        if self.search_fields:
            filters['fields'] = self.search_fields
        if self.default_operator != "OR":
            filters["default_operator"] = self.default_operator
        if self.options:
            filters["options"] = self.options
        if self.synonyms:
            filters["synonyms"] = self.synonyms
        if self.stopwords:
            filters["stopwords"] = self.stopwords
        if self.analyzer:
            filters["analyzer"] = self.analyzer
        if self.analyzer:
            filters["analyzer"] = self.analyzer
        if not self.allow_leading_wildcard:
            filters["allow_leading_wildcard"] = self.allow_leading_wildcard
        if not self.lowercase_expanded_terms:
            filters["lowercase_expanded_terms"] = self.lowercase_expanded_terms
        if not self.enable_position_increments:
            filters["enable_position_increments"] = self.enable_position_increments
        if self.fuzzy_prefix_length:
            filters["fuzzy_prefix_length"] = self.fuzzy_prefix_length
        if self.fuzzy_min_sim != 0.5:
            filters["fuzzy_min_sim"] = self.fuzzy_min_sim
        if self.phrase_slop:
            filters["phrase_slop"] = self.phrase_slop
        if self.min_concept_size!=2:
            filters["min_concept_size"] = self.min_concept_size
        if self.max_concept_size!=4:
            filters["max_concept_size"] = self.max_concept_size
        if self.term_expansion_steps!=1:
            filters["term_expansion_steps"] = self.term_expansion_steps
            
        if self.boost!=1.0:
            filters["boost"] = self.boost
        if self.clean_text:
            query = clean_string(self.text)
            if not query:
                raise InvalidQuery("The query is empty")
            filters["query"] = query
        else:
            if not self.text.strip():
                raise InvalidQuery("The query is empty")
            filters["query"] = self.text            
        
        return {self._internal_name:filters}

    def add_option(self, text):
        """
        Add an option to language expansion.
        
        
        text should be one of the AVAILABLE_NLP_OPTIONS. 
        """
        if text not in self.options:
            self.options.append(text)

    def populate_from_profile(self, profile):
        
        if profile.min_concept_size!=2:
            self.min_concept_size = profile.min_concept_size
        if profile.max_concept_size!=4:
            self.max_concept_size = profile.max_concept_size
        if profile.term_expansion_steps!=1:
            self.term_expansion_steps = profile.term_expansion_steps

        for name in AVAILABLE_NLP_OPTIONS:
            value = getattr(profile, name, None)
            if value:
                self.options.append(name)

        if profile.use_abstract_highlighting:
            if self.highlight is None:
                self.highlight = HighLighter("<b>", "</b>")
            self.highlight.pre_tags = profile.abstract_highlighting_pre
            self.highlight.post_tags = profile.abstract_highlighting_post        
#        
#    #    language = models.ForeignKey(Language, null=True, blank=True)#, limit_choices_to = {'active': True})
##    use_global_stopwords = models.BooleanField(default=False, help_text=_('Use global stopwords'))
##    use_database_stopwords = models.BooleanField(default=False, help_text=_('Use database stopwords'))
#    use_locutions = models.BooleanField(default=False, help_text=_('Use locutions'))
##    use_global_locutions = models.BooleanField(default=False, help_text=_('Use global locutions'))
##    use_database_locutions = models.BooleanField(default=False, help_text=_('Use database locutions'))
#    use_transliteration = models.BooleanField(default=False, help_text=_('Use transliteration'))

