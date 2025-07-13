import os
import unittest
import tempfile

try:
    from automojo.configuration.configurationloader import ConfigurationLoader
    HAS_REQUESTS = True
except ModuleNotFoundError:
    ConfigurationLoader = None
    HAS_REQUESTS = False

class TestConfigurationLoader(unittest.TestCase):

    def test_load_configuration(self):
        if not HAS_REQUESTS:
            self.skipTest('requests library not available')
        with tempfile.TemporaryDirectory() as td:
            yaml_file = os.path.join(td, 'conf.yaml')
            json_file = os.path.join(td, 'conf.json')
            with open(yaml_file, 'w') as f:
                f.write('a: 1\n')
            with open(json_file, 'w') as f:
                f.write('{"b": 2}')

            loader = ConfigurationLoader([f'dir://{td}'])
            data_yaml = loader.load_configuration_from_file(yaml_file)
            data_json = loader.load_configuration_from_file(json_file)
            self.assertEqual(data_yaml['a'], 1)
            self.assertEqual(data_json['b'], 2)

            uri, conf = loader.load_configuration_by_name('conf')
            self.assertEqual(conf['a'], 1)
            self.assertTrue(uri.startswith('dir://'))

if __name__ == '__main__':
    unittest.main()
