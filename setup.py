from flight_tracker import __version__
from setuptools import setup

with open('README.md', 'r') as readme_file:
    readme = readme_file.read()

with open('requirements.txt', 'r') as req_file:
    requirements = [x.strip() for x in req_file.readlines()]

setup(
    name='flight_tracker',
    version=__version__,
    description='Track Southwest flights and optionally send notifications when prices drop.',
    long_description=readme,
    author="broadtoad",
    author_email='broadtoad@gmail.com',
    url='https://github.com/broadtoad/Flight_Tracker/',
    packages=[
        'flight_tracker',
    ],
    package_dir={'flight_tracker': 'flight_tracker'},
    include_package_data=True,
    data_files=[('', ['twilio.json'])],
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords="flights tracker",
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    entry_points={
        'console_scripts': ['flight_tracker=flight_tracker.flight_tracker:main'],
    },
)
