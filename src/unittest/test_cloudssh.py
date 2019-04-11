
import os
import tempfile
from unittest import mock
from hashlib import sha1
from random import random

import argparse

from .base import BaseTest
from .. import cloudssh


class Test(BaseTest):

    fake_reservations = [
        {
            'Groups': [],
            'Instances': [
                {
                    'InstanceId': 'i-' + sha1(str(random()).encode('utf-8')).hexdigest()[:18],
                    'PrivateIpAddress': '10.0.0.60',
                    'PublicIpAddress': '123.456.7.89',
                    'State': {
                        'Code': 16,
                        'Name': 'running'
                    },
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': 'test_instance'
                        }
                    ]
                },
                {
                    'InstanceId': 'i-' + sha1(str(random()).encode('utf-8')).hexdigest()[:18],
                    'PrivateIpAddress': '10.0.0.61',
                    'PublicIpAddress': '123.456.7.90',
                    'State': {
                        'Code': 16,
                        'Name': 'running'
                    },
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': 'test_instance_2'
                        }
                    ]
                },
                {
                    'InstanceId': 'i-' + sha1(str(random()).encode('utf-8')).hexdigest()[:18],
                    'PrivateIpAddress': '10.0.0.62',
                    'PublicIpAddress': '123.456.7.91',
                    'State': {
                        'Code': 80,
                        'Name': 'stopped'
                    },
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': 'test_instance_stopped'
                        }
                    ]
                },
                {
                    'InstanceId': 'i-' + sha1(str(random()).encode('utf-8')).hexdigest()[:18],
                    'PrivateIpAddress': '10.0.0.63',
                    'PublicIpAddress': '123.456.7.94',
                    'State': {
                        'Code': 16,
                        'Name': 'running'
                    }
                },
                {
                    'InstanceId': 'i-' + sha1(str(random()).encode('utf-8')).hexdigest()[:18],
                    'PrivateIpAddress': '10.0.0.64',
                    'PublicIpAddress': '123.456.7.95',
                    'State': {
                        'Code': 16,
                        'Name': 'running'
                    },
                    'Tags': [
                        {
                            'Key': 'env',
                            'Value': 'prod'
                        }
                    ]
                }
            ]
        }
    ]

    test_config = """
        [MAIN]

        region = us-east-1
        aws_profile_name = cloud_ssh_unittest
        ssh_user = paul
    """

    def setUp(self):
        # Set unit tests config dir
        self.tmp_config_dir = tempfile.TemporaryDirectory()
        cloudssh.config_dir = self.tmp_config_dir.name + '/'

        # Write default config
        with open(cloudssh.config_dir + 'cloudssh.cfg', 'w') as f:
            f.write(self.test_config)

        # Parse config
        cloudssh.parse_user_config()

        # Set region
        cloudssh.set_region()

    def tearDown(self):
        # Cleanup temp dir
        self.tmp_config_dir.cleanup()

    @mock.patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(region=None, build_index=None, instance='my_server'))
    def test_parse_cli_args(self, mock_args):

        args = cloudssh.parse_cli_args()

        assert type(args) is dict
        assert args['region'] is None  # defaulted to None
        assert args['build_index'] is False  # defaulted to False

    def test_parse_user_config(self):

        # Config file exists
        assert isinstance(cloudssh.parse_user_config(), object)

        # Config file does not exists
        assert cloudssh.parse_user_config(filename='invalid.cfg') is None

    def test_get_value_from_user_config(self):

        # Get a valid config
        assert cloudssh.get_value_from_user_config(
            'aws_profile_name') == 'cloud_ssh_unittest'

        # We should get None with an invalid config
        assert cloudssh.get_value_from_user_config('invalid') is None

        # We should get None if we don't have a loaded config
        cloudssh.user_config = None
        assert cloudssh.get_value_from_user_config('aws_profile_name') is None

    def test_set_region(self):

        # From config file
        assert cloudssh.set_region() == 'us-east-1'

        # Region sent from CLI
        assert cloudssh.set_region(from_args='us-west-1') == 'us-west-1'

        # Invalid region name
        self.assertRaises(RuntimeError, cloudssh.set_region, 'us-invalid-1')

    @mock.patch.object(cloudssh, 'get_value_from_user_config', return_value=None)
    def test_set_region_2(self, mock_args):

        # Test default without CLI input or config file
        assert cloudssh.set_region() == 'us-east-1'

    def test_get_aws_client(self):

        client = cloudssh.get_aws_client()

        # assert isinstance(client, botocore.client.EC2)
        assert isinstance(client, object)

    def test_is_instance_id(self):

        assert cloudssh.is_instance_id('i-68602df5') is True
        assert cloudssh.is_instance_id('i-015baacc848a0brfg') is True
        assert cloudssh.is_instance_id('this_is_a_name') is False

    def test_aws_lookup(self):

        client = cloudssh.get_aws_client()

        # Lookup an instance name
        response = cloudssh.aws_lookup(
            instance='cloudssh_test_instance', client=client)
        assert isinstance(response, dict)
        assert isinstance(response['Reservations'], list)

        # lookup an instance ID
        response = cloudssh.aws_lookup(
            instance='i-06bb6dbab77bfcf3f', client=client)
        assert isinstance(response, dict)
        assert isinstance(response['Reservations'], list)

    def test_get_public_ip(self):

        assert cloudssh.get_public_ip(
            reservations=self.fake_reservations) == '123.456.7.89'

        # No reservations
        self.assertRaises(SystemExit, cloudssh.get_public_ip, reservations=[])

        # Reservations but no public IP
        altered = self.fake_reservations
        altered[0]['Instances'][0].pop('PublicIpAddress')
        self.assertRaises(SystemExit, cloudssh.get_public_ip,
                          reservations=altered)

    def test_get_ssh_command(self):
        assert cloudssh.get_ssh_command(public_ip='123.456.7.89') == [
            'ssh', '123.456.7.89']

        assert cloudssh.get_ssh_command(
            public_ip='123.456.7.89',
            user='paul'
        ) == ['ssh', 'paul@123.456.7.89']

    def test_resolve_home(self):

        assert cloudssh.resolve_home('/tmp/full/path') == '/tmp/full/path'
        assert cloudssh.resolve_home(
            '~/in_home').startswith(('/home/', '/Users'))

    def test_is_dir(self):

        assert cloudssh.is_dir('/tmp/nonexistent') is False
        assert cloudssh.is_dir('/tmp/') is True

    def test_mkdir(self):

        test_dir = '/tmp/test_mkdir'

        assert cloudssh.mkdir(test_dir) is True

        os.rmdir(test_dir)

    def test_get_instance_names(self):

        assert cloudssh.get_instance_names(
            reservations=self.fake_reservations) == ['test_instance', 'test_instance_2']

        # No reservations
        self.assertRaises(
            SystemExit, cloudssh.get_instance_names, reservations=[])

    def test_read_index(self):

        filename = 'test_read_file'

        cloudssh.write_index(
            filename=filename,
            content={'a': True}
        )

        # Read file
        assert cloudssh.read_index(filename=filename) == {'a': True}

        # Read invalid file
        assert cloudssh.read_index(filename='/tmp/nonexistent') == {}

    def test_write_index(self):

        filename = 'test_write_index'

        assert cloudssh.write_index(
            filename=filename,
            content={}
        ) is True

    @mock.patch.object(cloudssh, 'get_value_from_user_config', return_value='my_profile')
    def test_append_to_index(self, mock_args):

        cloudssh.region = 'us-east-1'

        # With an existing index
        assert cloudssh.append_to_index(
            existing_index={
                'my_profile': {
                    'us-west-1': ['name_123']
                }
            },
            new=['name_1', 'name_2']
        ) == {
            'my_profile': {
                'us-west-1': ['name_123'],
                'us-east-1': ['name_1', 'name_2'],
            }
        }

        # Without an existing index
        assert cloudssh.append_to_index(
            existing_index={},
            new=['name_1', 'name_2']
        ) == {
            'my_profile': {
                'us-east-1': ['name_1', 'name_2'],
            }
        }

    def test_build_index(self):

        filename = 'test_index'

        assert cloudssh.build_index(filename=filename) is True

        # Build index with config dir creation
        with tempfile.TemporaryDirectory() as test_dir:
            cloudssh.config_dir = test_dir + '/new_path/'
            assert cloudssh.build_index(filename=filename) is True

    def test_get_autocomplete_values(self):

        filename = 'test_get_autocomplete_values'

        cloudssh.region = 'us-east-1'

        # Write test index
        cloudssh.write_index(
            filename=filename,
            content={
                'cloud_ssh_unittest': {
                    'us-west-1': ['name_123'],
                    'us-east-1': ['name_1', 'name_2'],
                }
            }
        )

        assert cloudssh.get_autocomplete_values(filename=filename) == [
            'name_1', 'name_2']

    @mock.patch.object(cloudssh, 'get_value_from_user_config', return_value='nonexistent_profile')
    def test_get_autocomplete_values_2(self, mock_args):

        filename = 'test_get_autocomplete_values'

        assert cloudssh.get_autocomplete_values(filename=filename) == []
