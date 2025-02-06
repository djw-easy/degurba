from setuptools import setup, find_packages

setup(
    name='degurba',
    version='0.1',
    author='Your Name',
    author_email='djw@lreis.ac.cn',
    description='Urban Boundary Extraction Software Based on Degree of Urbanization',
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/djw-easy/degurba',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
    install_requires=[
        'rasterio',
        'scipy'
    ],
)