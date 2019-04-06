# cloudssh

[![Build Status](https://travis-ci.org/gabfl/cloudssh.svg?branch=master)](https://travis-ci.org/gabfl/cloudssh)
[![codecov](https://codecov.io/gh/gabfl/cloudssh/branch/master/graph/badge.svg)](https://codecov.io/gh/gabfl/cloudssh)
[![MIT licensed](https://img.shields.io/badge/license-MIT-green.svg)](https://raw.githubusercontent.com/gabfl/cloudssh/master/LICENSE)

EC2 SSH connections helper

## An SSH connection helper for AWS

`cloudssh` allows you to quickly connect to EC2 instances using their names or instance IDs.

It will call the AWS SDK to find the instance public IP address and open a SSH connection in a subprocess.

Example:

![EC2](https://github.com/gabfl/cloudssh/blob/master/img/ec2.png?raw=true)

You can connect to this instance with:
```
cloudssh dev
```

## Installation and usage

```bash
pip3 install cloudssh
aws configure # To configure your AWS credentials

cloudssh myserver # Call the module followed by the name of one of your servers
```

## Advanced configuration

You can optionally create a file `~/.cloudssh.cfg` (see [example](.cloudssh.cfg.sample)).
