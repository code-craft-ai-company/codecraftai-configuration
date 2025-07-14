import os
import unittest
import shutil
import tempfile

from automojo.configuration.configurationloader import ConfigurationLoader
class TestConfigurationLoader(unittest.TestCase):

    def setUp(self):
        self.configDirectory = tempfile.mkdtemp("config-tests")
        return

    def tearDown(self):
        if os.path.exists(self.configDirectory):
            shutil.rmtree(self.configDirectory, ignore_errors=True)
        return
    
    def test_load_json_configuration_by_fullfile(self):
        
        
        json_file = os.path.join(self.configDirectory, 'fullfile-conf.json')
        with open(json_file, 'w') as f:
            f.write('{"b": 2}')

        loader = ConfigurationLoader([])
        data_json = loader.load_configuration_from_file(json_file)
        self.assertEqual(data_json['b'], 2)
        return


    def test_load_json_configuration_by_name(self):

        json_file = os.path.join(self.configDirectory, 'nameonly-conf.json')
        with open(json_file, 'w') as f:
            f.write('{"b": 2}')

        loader = ConfigurationLoader([f'dir://{self.configDirectory}'])
        config_url, data_json = loader.load_configuration_by_name("nameonly-conf")
        self.assertEqual(data_json['b'], 2)

        return


    def test_load_yaml_configuration_by_fullfile(self):

        yaml_file = os.path.join(self.configDirectory, 'nameonly-conf.yaml')
        with open(yaml_file, 'w') as f:
            f.write('a: 1\n')
        
        loader = ConfigurationLoader([])
        data_yaml = loader.load_configuration_from_file(yaml_file)
        self.assertEqual(data_yaml['a'], 1)
        return
    
    
    def test_load_yaml_configuration_by_name(self):

        yaml_file = os.path.join(self.configDirectory, 'nameonly-conf.yaml')
        with open(yaml_file, 'w') as f:
            f.write('a: 1\n')
        
        loader = ConfigurationLoader([f'dir://{self.configDirectory}'])
        config_uri, data_yaml = loader.load_configuration_by_name("nameonly-conf")
        self.assertEqual(data_yaml['a'], 1)

        return

if __name__ == '__main__':
    unittest.main()
