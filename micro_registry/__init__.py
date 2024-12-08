#
# MIT License
#
# Copyright (c) 2024 Aleksander(Olek) Stanik
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction.
#
# See the LICENSE file for full license details.

__version__ = "0.4.3"


def init():
    """Initialize the micro registry by loading necessary modules."""
    import os

    from micro_registry.registry import load_modules_from_directory

    package_dir = os.path.dirname(os.path.abspath(__file__))
    # Load all modules from the package directory
    load_modules_from_directory(package_dir)
