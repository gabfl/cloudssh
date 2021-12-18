
import os
import sys
import tempfile
from unittest import mock
from hashlib import sha1
from random import random
from io import StringIO

import argparse

from .base import BaseTest
from .. import cloudssh


class Test(BaseTest):

    # This is a real instance in the real test account
    # Might need updating if the instance becomes unavailable
    real_instance = {
        'id': 'i-0d1ab7cd99158dfb5',
        'public_ip': '3.84.141.144',
        'private_ip': '172.31.81.127',
        'type': 't1.micro',
                'vpc': 'vpc-37911a4d',
                'subnet': 'subnet-e4f389ca',
                'launch_date': '2021-12-18 15:21:23+00:00',
                'tags': [{'Key': 'Name', 'Value': 'cloudssh_test_instance'}]
    }

    fake_reservations = [
        {
            'Groups': [],
            'Instances': [
                {
                    'InstanceId': 'i-b929323f777f4c016d',
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
                    'InstanceId': 'i-2959b4a6e3cdd13a2f',
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
                return_value=argparse.Namespace(region=None, build_index=None, instance='my_server', search=None, info=None))
    def test_parse_cli_args(self, mock_args):

        args = cloudssh.parse_cli_args()

        assert type(args) is dict
        assert args['region'] is None  # defaulted to None
        assert args['build_index'] is False  # defaulted to False
        assert args['info'] is None  # defaulted to None

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
            instance=self.real_instance['id'], client=client)
        assert isinstance(response, dict)
        assert isinstance(response['Reservations'], list)

    def test_get_instance_infos(self):

        assert cloudssh.get_instance_infos(
            reservations=self.fake_reservations) == {
                'id': 'i-b929323f777f4c016d',
                'launch_date': None,
                'private_ip': '10.0.0.60',
                'public_ip': '123.456.7.89',
                'subnet': None,
                'tags': [{'Key': 'Name', 'Value': 'test_instance'}],
                'type': None,
                'vpc': None
        }

        # No reservations
        self.assertRaises(
            SystemExit, cloudssh.get_instance_infos, reservations=[])

        # Reservations but no public IP
        altered = self.fake_reservations
        altered[0]['Instances'][0].pop('PublicIpAddress')
        self.assertRaises(SystemExit, cloudssh.get_instance_infos,
                          reservations=altered)

    def test_get_ssh_command(self):
        assert cloudssh.get_ssh_command(public_ip='123.456.7.89') == [
            'ssh', '123.456.7.89']

        assert cloudssh.get_ssh_command(
            public_ip='123.456.7.89',
            user='paul'
        ) == ['ssh', 'paul@123.456.7.89']

        assert cloudssh.get_ssh_command(
            public_ip='123.456.7.89',
            proxyjump='1.2.3.4'
        ) == ['ssh', '-J 1.2.3.4', '123.456.7.89']

        assert cloudssh.get_ssh_command(
            public_ip='123.456.7.89',
            flag='-v'
        ) == ['ssh', 'v', '123.456.7.89']

        assert cloudssh.get_ssh_command(
            public_ip='123.456.7.89',
            user='paul',
            proxyjump='1.2.3.4',
            flag='-v'
        ) == ['ssh', '-J 1.2.3.4', 'v', 'paul@123.456.7.89']

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

    def test_get_instances_list(self):

        assert cloudssh.get_instances_list(
            reservations=self.fake_reservations) == [
                {
                    'name': 'test_instance',
                    'detail': {
                        'id': 'i-b929323f777f4c016d',
                        'public_ip': None,
                        'private_ip': '10.0.0.60',
                        'type': None,
                        'vpc': None,
                        'subnet': None,
                        'launch_date': None,
                        'tags': [{'Key': 'Name', 'Value': 'test_instance'}]
                    }
                }, {
                    'name': 'test_instance_2',
                    'detail': {
                        'id': 'i-2959b4a6e3cdd13a2f',
                        'public_ip': '123.456.7.90',
                        'private_ip': '10.0.0.61',
                        'type': None,
                        'vpc': None,
                        'subnet': None,
                        'launch_date': None,
                        'tags': [{'Key': 'Name', 'Value': 'test_instance_2'}]
                    }
                }
        ]

        # No reservations
        self.assertRaises(
            SystemExit, cloudssh.get_instances_list, reservations=[])

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

    @mock.patch.object(cloudssh, 'get_instances_list_from_index', return_value=[{'name': 'one_thing', 'detail': {'publicIp': '123.456.789.0'}}, {'name': 'one_other_thing', 'detail': {'publicIp': '123.456.789.1'}}, {'name': 'third_thing', 'detail': {'publicIp': '123.456.789.2'}}])
    @mock.patch('src.cloudssh.confirm', return_value=True)
    def test_search_one_result(self, mock_args, mock_args_2):
        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out

            # Render file content to stdout
            cloudssh.search(query='other_thing')

            output = out.getvalue().strip()
            assert output == ''  # Because it was intercepted and never printed
        finally:
            sys.stdout = saved_stdout

    @mock.patch.object(cloudssh, 'get_instances_list_from_index', return_value=[{'name': 'one_thing', 'detail': {'publicIp': '123.456.789.0'}}, {'name': 'one_other_thing', 'detail': {'publicIp': '123.456.789.1'}}, {'name': 'third_thing', 'detail': {'publicIp': '123.456.789.2'}}])
    def test_search_multiple_results(self, mock_args):
        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out

            # Catch `exit()` and render content to stdout
            self.assertRaises(
                SystemExit, cloudssh.search, query='thing')

            output = out.getvalue().strip()
            assert output == 'Results:\n* one_thing\n* one_other_thing\n* third_thing'
        finally:
            sys.stdout = saved_stdout

    def test_search_no_result(self):
        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out

            # Catch `exit()` and render content to stdout
            self.assertRaises(
                SystemExit, cloudssh.search, query='invalid_name')

            output = out.getvalue().strip()
            assert output == 'No result!'
        finally:
            sys.stdout = saved_stdout

    def test_confirm(self):
        with mock.patch('builtins.input', return_value='y'):
            self.assertTrue(cloudssh.confirm())
            self.assertTrue(cloudssh.confirm(resp=True))

    def test_confirm_2(self):
        with mock.patch('builtins.input', return_value='n'):
            self.assertFalse(cloudssh.confirm())
            self.assertFalse(cloudssh.confirm(resp=True))

    def test_confirm_3(self):
        # Test empty return
        with mock.patch('builtins.input', return_value=''):
            self.assertTrue(cloudssh.confirm(resp=True))

    def test_get_instances_list_from_index(self):

        filename = 'test_get_instances_list_from_index'

        cloudssh.region = 'us-east-1'

        # Write test index
        cloudssh.write_index(
            filename=filename,
            content={
                'cloud_ssh_unittest': {
                    'us-west-1': [{'name': 'name_123'}],
                    'us-east-1': [{'name': 'name_1'}, {'name': 'name_2'}],
                }
            }
        )

        assert cloudssh.get_instances_list_from_index(filename=filename) == [
            {'name': 'name_1'}, {'name': 'name_2'}]

    @mock.patch.object(cloudssh, 'get_value_from_user_config', return_value='nonexistent_profile')
    def test_get_instances_list_from_index_2(self, mock_args):

        filename = 'test_get_instances_list_from_index'

        assert cloudssh.get_instances_list_from_index(filename=filename) == []

    @mock.patch.object(cloudssh, 'get_instances_list_from_index', return_value=[{'name': 'one_thing'}, {'name': 'one_other_thing'}, {'name': 'third_thing'}, {'name': 'with space'}])
    @mock.patch('readline.get_line_buffer', return_value='one')
    def test_autocomplete(self, mock_args, mock_args_2):

        assert cloudssh.autocomplete('on', state=0) == 'one_thing'
        assert cloudssh.autocomplete(
            'on', state=1) == 'one_other_thing'
        assert cloudssh.autocomplete('on', state=2) is None

    @mock.patch.object(cloudssh, 'get_instances_list_from_index', return_value=[{'name': 'one_thing'}, {'name': 'one_other_thing'}, {'name': 'third_thing'}, {'name': 'with space'}])
    @mock.patch('readline.get_line_buffer', return_value='with ')
    def test_autocomplete_2(self, mock_args, mock_args_2):

        assert cloudssh.autocomplete('on', state=0) == 'space'

    @mock.patch.object(cloudssh, 'get_instances_list_from_index', return_value=[{'name': 'one_thing'}, {'name': 'one_other_thing'}, {'name': 'third_thing'}])
    @mock.patch('readline.get_line_buffer', return_value='ONE')
    def test_autocomplete_3(self, mock_args, mock_args_2):

        assert cloudssh.autocomplete(
            'on', state=0, is_case_sensitive=True) is None

    @mock.patch.object(cloudssh, 'get_instances_list_from_index', return_value=[{'name': 'one_thing'}, {'name': 'one_other_thing'}, {'name': 'third_thing'}])
    @mock.patch('readline.get_line_buffer', return_value='ONE')
    def test_autocomplete_4(self, mock_args, mock_args_2):

        assert cloudssh.autocomplete('on', state=0) == 'one_thing'
        assert cloudssh.autocomplete(
            'on', state=1) == 'one_other_thing'
        assert cloudssh.autocomplete('on', state=2) is None

    @mock.patch.object(cloudssh, 'get_instances_list_from_index', return_value=[{'name': 'one_thing'}, {'name': 'one_other_thing'}, {'name': 'third_thing'}])
    @mock.patch('builtins.input', return_value='some_value')
    def test_get_input_autocomplete(self, mock_args, mock_args_2):

        assert cloudssh.get_input_autocomplete() == 'some_value'

    @mock.patch.object(cloudssh, 'get_instances_list_from_index', return_value=[{'name': 'one_thing', 'detail': {'public_ip': '123.456.789.0'}}, {'name': 'one_other_thing', 'detail': {'public_ip': '123.456.789.1'}}, {'name': 'third_thing', 'detail': {'public_ip': '123.456.789.2'}}])
    def test_instance_lookup_index(self, mock_args):

        assert cloudssh.instance_lookup(
            'one_thing') == ('index', {'public_ip': '123.456.789.0'})

    @mock.patch.object(cloudssh, 'get_instances_list_from_index', return_value=[{'name': 'one_thing', 'detail': {'public_ip': '123.456.789.0'}}, {'name': 'one_other_thing', 'detail': {'public_ip': '123.456.789.1'}}, {'name': 'third_thing', 'detail': {'public_ip': '123.456.789.2'}}])
    def test_instance_lookup_aws(self, mock_args):

        assert cloudssh.instance_lookup(
            'cloudssh_test_instance') == ('aws', self.real_instance)
