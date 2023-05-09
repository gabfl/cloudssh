from setuptools import setup

import pypandoc


setup(
    name='cloudssh',
    version='1.4',
    description='EC2 SSH connections helper',
    long_description=pypandoc.convert_file('README.md', 'rst'),
    author='gab',
    author_email='gab@confiant.com',
    url='https://github.com/gabfl/cloudssh',
    packages=['cloudssh'],
    package_dir={'cloudssh': 'src'},
    install_requires=['argparse', 'boto3'],  # external dependencies
    entry_points={
        'console_scripts': [
            'cloudssh = cloudssh.cloudssh:main',
            'cssh = cloudssh.cloudssh:main',
        ],
    },
    classifiers=[  # see https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',
        # 'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Natural Language :: English',
        # 'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
    ],
)
