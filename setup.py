from setuptools import setup, find_packages

setup(
    name='cartlis',
    version='0.1.0',
    packages=find_packages(),  # This will automatically find the 'cartlis' package
    include_package_data=True,
    install_requires=[
        'pyyaml',
        'openapi-spec-validator',
        'python-dotenv',
        'requests'
    ],
    entry_points={
        'console_scripts': [
            'cartlis=cartlis.cartlis_governance:main',  # Use the new module path
        ],
    },
    python_requires='>=3.6',
)