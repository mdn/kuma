import unittest
from nose.plugins import Plugin
from nose.plugins.manager import DefaultPluginManager

class OverridesSkip(Plugin):
    """Plugin to override the built-in Skip"""
    enabled = True
    name = 'skip'
    is_overridden = True


class TestDefaultPluginManager(unittest.TestCase):

    def test_extraplugins_override_builtins(self):
        pm = DefaultPluginManager()
        pm.addPlugins(extraplugins=[OverridesSkip()])
        pm.loadPlugins()
        for plugin in pm.plugins:
            if plugin.name == "skip":
                break
        overridden = getattr(plugin, 'is_overridden', False)
        self.assertTrue(overridden)
