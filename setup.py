from setuptools import setup, find_packages

setup(
    name="micro-registry",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pyyaml',
    ],
    author="Aleksander Stanik (Olek)",
    author_email="aleksander.stanik@hammerheadsengineers.com",
    description="A Python library for managing and loading class instances from modules and YAML configurations.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/AleksanderStanikHE/micro-registry.git",
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
