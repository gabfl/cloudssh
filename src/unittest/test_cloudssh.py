
from unittest import mock

import argparse

from .base import BaseTest
from .. import cloudssh


class Test(BaseTest):

    fake_reservations = [
        {
            'Groups': [],
            'Instances': [
                {
                    'AmiLaunchIndex': 0,
                    'InstanceId': 'i-8747641e',
                    'InstanceType': 'm4.large',
                    'KeyName': 'us-east-1-keypair-nate',
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
                    'AmiLaunchIndex': 0,
                    'InstanceId': 'i-87056lbe',
                    'InstanceType': 'm4.large',
                    'KeyName': 'us-east-1-keypair-nate',
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
                }
            ]
        }
    ]

    @mock.patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(region=None, build_index=None, instance='my_server'))
    def test_parse_cli_args(self, mock_args):
        cloudssh.set_region()
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
        cloudssh.parse_user_config()
        assert isinstance(cloudssh.get_value_from_user_config(
            'aws_profile_name'), str)
        assert cloudssh.get_value_from_user_config('invalid') is None

    def test_set_region(self):

        # Default region
        assert cloudssh.set_region() == 'us-east-1'

        # Region sent from CLI
        assert cloudssh.set_region(from_args='us-west-1') == 'us-west-1'

        # Invalid region name
        self.assertRaises(RuntimeError, cloudssh.set_region, 'us-invalid-1')

    def test_get_aws_client(self):

        cloudssh.set_region()
        client = cloudssh.get_aws_client()

        # assert isinstance(client, botocore.client.EC2)
        assert isinstance(client, object)

    def test_is_instance_id(self):

        assert cloudssh.is_instance_id('i-68602df5') is True
        assert cloudssh.is_instance_id('i-015baacc848a0brfg') is True
        assert cloudssh.is_instance_id('this_is_a_name') is False

    def test_aws_lookup(self):

        cloudssh.set_region()
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

        assert cloudssh.mkdir('/tmp/test_dir') is True

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
        cloudssh.delete_index(filename=filename)

        # Read invalid file
        assert cloudssh.read_index(filename='/tmp/nonexistent') == {}

    def test_write_index(self):

        filename = 'test_write_index'

        assert cloudssh.write_index(
            filename=filename,
            content={}
        ) is True
        cloudssh.delete_index(filename=filename)

    def test_delete_index(self):

        filename = 'test_delete_index'

        cloudssh.write_index(filename=filename)
        assert cloudssh.delete_index(filename=filename) is True

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
        cloudssh.delete_index(filename=filename)
