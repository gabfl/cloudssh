# cloudssh

[![Build Status](https://travis-ci.org/gabfl/cloudssh.svg?branch=main)](https://travis-ci.org/gabfl/cloudssh)
[![codecov](https://codecov.io/gh/gabfl/cloudssh/branch/main/graph/badge.svg)](https://codecov.io/gh/gabfl/cloudssh)
[![MIT licensed](https://img.shields.io/badge/license-MIT-green.svg)](https://raw.githubusercontent.com/gabfl/cloudssh/main/LICENSE)

EC2 SSH connections helper

## An SSH connection helper for AWS

`cloudssh` allows you to quickly connect to EC2 instances using their names or instance IDs.

It will call the AWS SDK to find the instance public IP address and open a SSH connection in a subprocess.

Example:

![EC2](https://github.com/gabfl/cloudssh/blob/main/img/ec2.png?raw=true)

You can connect to this instance with:
```
cssh dev
```

You can also use the **auto-completion feature** by building a local index of your AWS instances then calling `cloudssh` without any argument.
```
cssh --build_index
# The instances index has been stored in ~/.cloudssh/.

cssh
# Start typing an instance name and press [TAB] to auto complete.
```

Or search instances by name with:
```
cssh --build_index
# The instances index has been stored in ~/.cloudssh/.

cssh --search http
# Found "web-http-prod", connect? [Y/n]: 
```

Or lookup an instance details:
```
cssh web-http-prod --info
# * Network
# Public ID: 123.***.***.***
# Private ID: 10.***.***.***
#
# * VPC/subnet
# VPC ID: vpc-******
# Subnet ID: subnet-******
#
# * Misc
# Instance name: web-http-prod
# Instance ID: i-******
# Instance type: t2.xlarge
# Launch date: 2019-10-12 15:44:36+00:00
#
# * Tags
#   product = web_cluster
#   environment = production
#   Name = web-http-prod
```

Example:

![EC2](https://github.com/gabfl/cloudssh/blob/main/img/autocomplete_demo.gif?raw=true)

## Installation and usage

```bash
pip3 install cloudssh
aws configure # To configure your AWS credentials

cssh myserver # Call the module followed by the name of one of your servers
```

## Advanced configuration

You can optionally create a file `~/.cloudssh/cloudssh.cfg` (see [example](cloudssh.cfg.sample)).
