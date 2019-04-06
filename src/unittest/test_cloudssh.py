
import botocore

from .base import BaseTest
from .. import cloudssh


class Test(BaseTest):

    def test_get_regions(self):
        regions = cloudssh.get_regions()

        assert type(regions) == list
        assert 'us-east-1' in regions
        assert 'us-west-1' in regions

    def test_parse_cli_args(self):
        args = cloudssh.parse_cli_args()

        assert type(args) is dict
        assert args['region'] is None  # defaulted to None

    def test_parse_user_config(self):
        user_config = cloudssh.parse_user_config()

        assert isinstance(user_config, object)

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
        response = cloudssh.aws_lookup(instance='some_instance', client=client)

        assert isinstance(response, dict)
        assert isinstance(response['Reservations'], list)

    def test_get_public_ip(self):

        reservations = [
            {
                'Groups': [],
                'Instances': [
                    {'AmiLaunchIndex': 0,
                     'InstanceId': 'i-8747641e',
                     'InstanceType': 'm4.large',
                     'KeyName': 'us-east-1-keypair-nate',
                     'PrivateIpAddress': '10.0.0.60',
                     'PublicIpAddress': '123.456.7.89',
                     'State': {
                         'Code': 16,
                         'Name': 'running'}
                     }
                ]
            }
        ]

        assert cloudssh.get_public_ip(
            reservations=reservations) == '123.456.7.89'

        # No reservations
        self.assertRaises(SystemExit, cloudssh.get_public_ip, reservations=[])

        # Reservations but no public IP
        reservations[0]['Instances'][0].pop('PublicIpAddress')
        self.assertRaises(SystemExit, cloudssh.get_public_ip,
                          reservations=reservations)
