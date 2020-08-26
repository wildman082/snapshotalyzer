from setuptools import setup

setup(
    name='snapshotalyzer',
    version="0.1",
    author='wildman',
    description='shotty manages AWS ec2 snapshots',
    packages=['shotty'],
    url='https://github.com/wildman082/snapshotalyzer',
    install_requires=[
        'click'
        'boto3'
    ],
    entry_points={  
        'console_scripts': [  
            'shotty=shotty.shotty:cli',  
        ]  
    },
)