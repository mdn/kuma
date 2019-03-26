from django.db import models
from django.utils.translation import ugettext_lazy as _


class Banner(models.Model):
    """
    Defines the model for a single call to action banner
    """
    THEME_DEFAULT = 'default'
    THEME_GRADIENT = 'gradient'
    THEME_DINOHEAD = 'dinohead'
    THEMES = (
        (THEME_DEFAULT, 'Default'),
        (THEME_GRADIENT, 'Gradient'),
        (THEME_DINOHEAD, 'Dinohead')
    )
    banner_name = models.CharField(verbose_name=_(u'Banner Name'), max_length=50)
    banner_title = models.CharField(verbose_name=_(u'Banner Title'), max_length=100)
    banner_copy = models.TextField(verbose_name=_(u'Main Copy'),
                                   help_text=_('Main call to action copy has a 200 character limit'),
                                   max_length=200)
    banner_button_copy = models.CharField(verbose_name=_(u'Button Copy'), max_length=50)
    banner_theme = models.CharField(verbose_name=_(u'Theme'), max_length=20,
                                    choices=THEMES, default=THEME_DEFAULT)
    banner_active = models.BooleanField(verbose_name=_(u'Activate'))
    banner_priority = models.PositiveSmallIntegerField(verbose_name=_(u'Priority (1-100)'),
                                                       default=100)

    def __str__(self):
        return self.banner_name
