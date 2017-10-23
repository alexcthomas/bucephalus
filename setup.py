from setuptools import setup, find_packages

setup(
    name='bucephalus',
    version='0.8.0',
    description='A dynamic web frontend for displaying data',
    long_description='A web frontend for displaying graphs (centering on highcharts) and other content, organised into pages, with a nav pane',
    url='https://github.com/alexcthomas/bucephalus',
    author='Alex Thomas',
    author_email='alexthomas00@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Framework :: Flask',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content'
    ],
    keywords='data visualisation',
    python_requires='>=3',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['flask', 'pandas', 'seaborn', 'scipy', 'ujson'],
    package_data={
        'sample': ['static', 'templates', 'views'],
    }
)