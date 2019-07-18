from setuptools import setup, find_packages

setup(
    name='pyares',
    version='0.2.0',
    # packages=['pyares'],
    packages=find_packages(exclude=["tests", "docs", "dev", "dist"]),
    #package_dir={'pyares':','},
    url='',
    license='MIT',
    author='Esther Kok',
    author_email='esther.kok@esa.int',
    description='Python ARES Dataprovision API',
    python_requires='>=3.3,<4',
    install_requires=['happybase == 1.1.0',
                      'PyMySQL == 0.8.0',
                      'protobuf == 3.0.0',
                      'pyarrow == 0.9.0',
                      'pandas ==0.20.3 ',
                      'numpy == 1.14.5'],
    #exclude_package_data={'pyares':['data/*', 'conf/*']}
    #package_data={'pyares':['*']},# 'conf':['*.ini']}, #
    #package_data={'data':['venv.zip', 'pyares.pkl'], 'conf': ['pyares_conf.ini']}, #
    include_package_data=True
)
