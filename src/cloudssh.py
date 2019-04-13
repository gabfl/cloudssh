import boto3
import argparse
import subprocess
import configparser
from sys import argv, exit
import os
import json
import readline

region = None
user_config = None
config_dir = '~/.cloudssh/'

# Sourced from https://docs.aws.amazon.com/general/latest/gr/rande.html
regions = ['us-east-2', 'us-east-1', 'us-west-1', 'us-west-2', 'ap-south-1',
           'ap-northeast-3', 'ap-northeast-2', 'ap-southeast-1', 'ap-southeast-2',
           'ap-northeast-1', 'ca-central-1', 'cn-north-1', 'cn-northwest-1',
           'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-north-1', 'sa-east-1']


def parse_cli_args():
    """ Parse optional argparse arguments """

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--region", type=str,
                        help="Region", choices=regions, nargs='?')
    parser.add_argument('instance', nargs='*')
    parser.add_argument("-b", "--build_index", action='store_true',
                        help="Build a local index of your AWS instances")
    args = parser.parse_args()

    return {
        'region': args.region,
        'instance': args.instance[0] if type(args.instance) is list and len(args.instance) > 0 else None,
        'build_index': args.build_index if args.build_index else False,
    }


def parse_user_config(filename='cloudssh.cfg'):
    """ Read user config file """

    global user_config

    # Get full config file path
    full_path = resolve_home(config_dir) + filename

    user_config = None
    if os.path.isfile(full_path):
        config = configparser.ConfigParser()
        config.read(full_path)
        user_config = config['MAIN']

    return user_config


def get_value_from_user_config(item):
    """ Return an item from the user config or None """

    if user_config:
        try:
            return user_config[item]
        except KeyError:
            pass


def set_region(from_args=None, default='us-east-1'):
    """ Set AWS region """

    global region

    if from_args:  # Read from CLI args
        region = from_args
    # Read from config file
    elif get_value_from_user_config('region') is not None:
        region = get_value_from_user_config('region')
    else:
        region = default

    if region not in regions:
        raise RuntimeError('%s is not a valid AWS region' % (region))

    return region


def get_aws_client():
    """ Return an instance of the AWS client """

    # Client connection
    session = boto3.Session(
        profile_name=get_value_from_user_config('aws_profile_name'))
    return session.client("ec2", region_name=region)


def is_instance_id(instance):
    """ Return True if the user input is an instance ID instead of a name """

    if instance[:2] == 'i-':
        return True

    return False


def aws_lookup(client, instance=None, max_results=5):
    """ Lookup for instances in AWS """

    Filters = []

    if instance:
        if is_instance_id(instance) is False:  # Lookup by name
            Filters = [
                {
                    'Name': 'tag:Name',
                    'Values': [instance]
                },
            ]
        else:  # Lookup by AWS instance ID
            return client.describe_instances(
                InstanceIds=[instance]
            )

    # Search instances
    if max_results:
        response = client.describe_instances(
            Filters=Filters,
            MaxResults=max_results
        )
    else:
        response = client.describe_instances(
            Filters=Filters
        )

    return response


def get_public_ip(reservations):
    """ Get instance public IP """

    if len(reservations) == 0:
        print('No instance found matching this name or instance ID.')
        exit()

    # Get first instance
    reservation = reservations[0]['Instances'][0]

    if reservation.get('PublicIpAddress'):
        return reservation['PublicIpAddress']

    print('No public IP found for this instance.')
    exit()


def get_ssh_command(public_ip, user=None):
    """ Return SSH command  """

    if user:
        connection_string = '%s@%s' % (user, public_ip)
    else:
        connection_string = public_ip

    return ['ssh', '%s' % (connection_string)]


def ssh_subprocess(ssh_command):
    """ Open an ssh subprocess """

    subprocess.call(ssh_command)


def resolve_home(path):
    """ Resolve the user home directory """

    if path[:1] == '~':
        return os.path.expanduser('~') + path[1:]

    return path


def is_dir(path):
    """ Returns True if a directory exists """

    return os.path.isdir(resolve_home(path))


def mkdir(path):
    """ Create a directory """

    os.makedirs(resolve_home(path))

    return True


def get_instance_names(reservations):
    """ Return a list of instance names from reservations """

    if len(reservations) == 0:
        print('No instances found.')
        exit()

    # List instances
    names = []
    for reservation in reservations:
        for instance in reservation['Instances']:
            # Skip non running instances
            if instance.get('State') and instance['State'].get('Name', '') != 'running':
                continue

            # Lookup instance name
            if instance.get('Tags') and len(instance['Tags']) > 0:
                for tag in instance['Tags']:
                    if tag.get('Key') and tag['Key'] == 'Name' and tag['Value'] not in names:
                        names.append(tag['Value'])

    return names


def read_index(filename):
    """ Read index file """

    if os.path.isfile(resolve_home(config_dir) + filename):
        with open(resolve_home(config_dir) + filename, 'r') as f:
            content = f.read()
            return json.loads(content)

    return {}


def write_index(filename, content={}):
    """ Write index file """

    with open(resolve_home(config_dir) + filename, 'w') as f:
        content = json.dumps(content)
        f.write(content)

        return True


def append_to_index(existing_index, new):
    """ Add new values to the index """

    # Set profile name
    profile_name = get_value_from_user_config('aws_profile_name') or 'default'

    if not existing_index.get(profile_name):
        existing_index[profile_name] = {}

    existing_index[profile_name][region] = new

    return existing_index


def build_index(filename='index.json'):
    """ Build instance index """

    # Create config directory if necessary
    if not is_dir(config_dir):
        mkdir(config_dir)

    # Read existing index
    index = read_index(filename)

    # Get instances list
    response = aws_lookup(
        client=get_aws_client(),
        max_results=None
    )

    # Get instance names
    names = get_instance_names(response['Reservations'])

    # Build new index
    index = append_to_index(index, names)

    # Write index to file
    write_index(filename=filename, content=index)

    return True


def get_autocomplete_values(filename='index.json'):

    # Read index
    index = read_index(filename)

    # Set profile name
    profile_name = get_value_from_user_config('aws_profile_name') or 'default'

    # If there is no data for this profile name, return an empty list
    if not index.get(profile_name):
        return []

    return index[profile_name].get(region, [])


def autocomplete(text, state, is_case_sensitive=False):
    """ Generic readline completion entry point. """

    buffer = readline.get_line_buffer()

    completion_list = comp = get_autocomplete_values()

    if not is_case_sensitive:
        buffer = buffer.lower()
        comp = [c.lower() for c in completion_list]

    results = [c for c in comp if c.startswith(buffer)] + [None]

    # Handle multi-word inputs by truncating strings at the last space
    if buffer.find(' ') > 0:
        strip_pos = buffer.rfind(' ') + 1
        results = [i[strip_pos:] for i in results if i is not None] + [None]

    return results[state]


def get_input_autocomplete(message=''):
    """ Allow user to type input and provide auto-completion """

    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(autocomplete)

    try:
        return input(message).strip()
    except KeyboardInterrupt:
        return False
    except Exception:  # Other Exception
        return False


def main():
    # Read user config
    parse_user_config()

    # Read CLI arguments
    args = parse_cli_args()

    # Set region
    set_region()

    # Build instance index
    if args['build_index']:
        build_index()
        print("The instances index has been stored in %s." %
              (config_dir))
        exit()

    # Read instance or request user input
    instance = args['instance']
    if args['instance'] is None:
        instance = get_input_autocomplete('Instance name of ID: ')

    if not instance:
        raise RuntimeError('Usage: cloudssh some_instance')

    # AWS instance lookup
    response = aws_lookup(
        client=get_aws_client(),
        instance=instance
    )

    # Fetch public IP address or exit with a graceful message
    public_ip = get_public_ip(response['Reservations'])

    # Open SSH connection in a subprocess
    ssh_command = get_ssh_command(
        public_ip=public_ip,
        user=get_value_from_user_config('ssh_user')
    )
    ssh_subprocess(ssh_command)


if __name__ == '__main__':
    main()
