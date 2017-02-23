#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

import unittest
import mock

from mkdocs import plugins
from mkdocs import utils
from mkdocs import config


class DummyPlugin(plugins.BasePlugin):
    config_scheme = (
        ('foo', config.config_options.Type(utils.string_types, default='default foo')),
        ('bar', config.config_options.Type(int, default=0))
    )

    def on_pre_page(self, content, **kwargs):
        """ prepend `foo` config value to page content. """
        return ' '.join((self.config['foo'], content))

    def on_post_nav(self, item, **kwargs):
        """ do nothing (return None) to not modify item. """
        return None


class TestPluginClass(unittest.TestCase):

    def test_valid_plugin_options(self):

        options = {
            'foo': 'some value'
        }

        expected = {
            'foo': 'some value',
            'bar': 0
        }

        plugin = DummyPlugin()
        errors, warnings = plugin.load_config(options)
        self.assertEqual(plugin.config, expected)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_invalid_plugin_options(self):

        plugin = DummyPlugin()
        errors, warnings = plugin.load_config({'foo': 42})
        self.assertEqual(len(errors), 1)
        self.assertIn('foo', errors[0])
        self.assertEqual(warnings, [])

        errors, warnings = plugin.load_config({'bar': 'a string'})
        self.assertEqual(len(errors), 1)
        self.assertIn('bar', errors[0])
        self.assertEqual(warnings, [])

        errors, warnings = plugin.load_config({'invalid_key': 'value'})
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn('invalid_key', warnings[0])


class TestPluginCollection(unittest.TestCase):

    def test_set_plugin_on_collection(self):
        collection = plugins.PluginCollection()
        plugin = DummyPlugin()
        collection['foo'] = plugin
        self.assertEqual(collection.items(), [('foo', plugin)])

    def test_set_multiple_plugins_on_collection(self):
        collection = plugins.PluginCollection()
        plugin1 = DummyPlugin()
        collection['foo'] = plugin1
        plugin2 = DummyPlugin()
        collection['bar'] = plugin2
        self.assertEqual(collection.items(), [('foo', plugin1), ('bar', plugin2)])

    def test_run_event_on_collection(self):
        collection = plugins.PluginCollection()
        plugin = DummyPlugin()
        plugin.load_config({'foo': 'new'})
        collection['foo'] = plugin
        self.assertEqual(collection.run_event('pre_page', 'page content'), 'new page content')

    def test_run_event_twice_on_collection(self):
        collection = plugins.PluginCollection()
        plugin1 = DummyPlugin()
        plugin1.load_config({'foo': 'new'})
        collection['foo'] = plugin1
        plugin2 = DummyPlugin()
        plugin2.load_config({'foo': 'second'})
        collection['bar'] = plugin2
        self.assertEqual(collection.run_event('pre_page', 'page content'),
                         'second new page content')

    def test_event_returns_None(self):
        collection = plugins.PluginCollection()
        plugin = DummyPlugin()
        plugin.load_config({'foo': 'new'})
        collection['foo'] = plugin
        self.assertEqual(collection.run_event('post_nav', 'nav item'), 'nav item')

    def test_run_undefined_event_on_collection(self):
        collection = plugins.PluginCollection()
        self.assertEqual(collection.run_event('pre_page', 'page content'), 'page content')

    def test_run_unknown_event_on_collection(self):
        collection = plugins.PluginCollection()
        self.assertRaises(KeyError, collection.run_event, 'unknown', 'page content')


MockEntryPoint = mock.Mock()
MockEntryPoint.configure_mock(**{'name': 'sample', 'load.return_value': DummyPlugin})


@mock.patch('pkg_resources.iter_entry_points', return_value=[MockEntryPoint])
class TestPluginConfig(unittest.TestCase):

    def test_plugin_config_without_options(self, mock_class):

        cfg = {'plugins': ['sample']}
        option = config.config_options.Plugins()
        cfg['plugins'] = option.validate(cfg['plugins'])

        self.assertIsInstance(cfg['plugins'], plugins.PluginCollection)
        self.assertIn('sample', cfg['plugins'])
        self.assertIsInstance(cfg['plugins']['sample'], plugins.BasePlugin)
        expected = {
            'foo': 'default foo',
            'bar': 0
        }
        self.assertEqual(cfg['plugins']['sample'].config, expected)

    def test_plugin_config_with_options(self, mock_class):

        cfg = {
            'plugins': [{
                'sample': {
                    'foo': 'foo value',
                    'bar': 42
                }
            }]
        }
        option = config.config_options.Plugins()
        cfg['plugins'] = option.validate(cfg['plugins'])

        self.assertIsInstance(cfg['plugins'], plugins.PluginCollection)
        self.assertIn('sample', cfg['plugins'])
        self.assertIsInstance(cfg['plugins']['sample'], plugins.BasePlugin)
        expected = {
            'foo': 'foo value',
            'bar': 42
        }
        self.assertEqual(cfg['plugins']['sample'].config, expected)

    def test_plugin_config_uninstalled(self, mock_class):

        cfg = {'plugins': ['uninstalled']}
        option = config.config_options.Plugins()
        self.assertRaises(config.base.ValidationError, option.validate, cfg['plugins'])

    def test_plugin_config_not_list(self, mock_class):

        cfg = {'plugins': 'sample'}  # should be a list
        option = config.config_options.Plugins()
        self.assertRaises(config.base.ValidationError, option.validate, cfg['plugins'])

    def test_plugin_config_multivalue_dict(self, mock_class):

        cfg = {
            'plugins': [{
                'sample': {
                    'foo': 'foo value',
                    'bar': 42
                },
                'extra_key': 'baz'
            }]
        }
        option = config.config_options.Plugins()
        self.assertRaises(config.base.ValidationError, option.validate, cfg['plugins'])

    def test_plugin_config_not_string_or_dict(self, mock_class):

        cfg = {
            'plugins': [('not a string or dict',)]
        }
        option = config.config_options.Plugins()
        self.assertRaises(config.base.ValidationError, option.validate, cfg['plugins'])

    def test_plugin_config_options_not_dict(self, mock_class):

        cfg = {
            'plugins': [{
                'sample': 'not a dict'
            }]
        }
        option = config.config_options.Plugins()
        self.assertRaises(config.base.ValidationError, option.validate, cfg['plugins'])
