from setuptools import setup
setup(
    name='loc_reg',
    version='1.0',
    author='Cui Chengyu',
    packages={'loc_reg'},
    # include_package_data=True,
    package_data={'loc_reg': ['utils/dicts/*']}
)