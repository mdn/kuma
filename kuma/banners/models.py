# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Banner(models.Model):
    """
    Defines the model for a single call to action banner
    """
    THEME_DEFAULT = 'cta-background-default'
    THEME_GRADIENT = 'cta-background-linear'
    THEME_DINOHEAD = 'cta-background-dinohead'
    THEMES = (
        (THEME_DEFAULT, 'Default'),
        (THEME_GRADIENT, 'Gradient'),
        (THEME_DINOHEAD, 'Dinohead')
    )
    name = models.CharField('Banner Name', max_length=50)
    title = models.CharField('Banner Title', max_length=100)
    main_copy = models.TextField('Main Copy', max_length=200)
    button_copy = models.CharField('Button Copy', max_length=50)
    button_url = models.URLField('URL')
    theme = models.CharField('Theme', max_length=40,
                             choices=THEMES, default=THEME_DEFAULT)
    active = models.BooleanField('Activate')
    priority = models.PositiveSmallIntegerField('Priority (1-100)',
                                                default=100)

    def __str__(self):
        return self.name
