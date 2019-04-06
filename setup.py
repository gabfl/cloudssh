from setuptools import setup

try:
    import pypandoc
    long_description = pypandoc.convert_file('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README.md').read()


setup(
    name='cloudssh',
    version='1.0.1',
    description='EC2 SSH connections helper',
    long_description=long_description,
    author='gab',
    author_email='gab@confiant.com',
    url='https://github.com/gabfl/cloudssh',
    packages=['cloudssh'],
    package_dir={'cloudssh': 'src'},
    install_requires=['argparse', 'boto3'],  # external dependencies
    entry_points={
        'console_scripts': [
            'cloudssh = cloudssh.cloudssh:main',
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
