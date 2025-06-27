from setuptools import setup, find_packages

setup(
    name="wifi_fortress",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'PyQt5==5.15.9',
        'scapy==2.5.0',
        'reportlab==4.0.4',
        'psutil==5.9.5',
        'netifaces==0.11.0',
        'cryptography==41.0.1',
    ],
    extras_require={
        'dev': [
            'pytest==7.4.0',
            'pytest-cov==4.1.0',
            'black==23.3.0',
            'pylint==2.17.4',
            'mypy==1.4.1',
        ],
    },
)
