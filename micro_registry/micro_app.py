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

import os
import sys
import signal
import time
import argparse

# Ensure the current and repository directories are in sys.path
current_dir = os.getcwd()
repo_root = os.path.abspath(os.path.join(current_dir, '.'))

if repo_root not in sys.path:
    sys.path.append(repo_root)

# Import necessary modules
import micro_registry
from micro_registry.registry import load_modules_from_directory
from micro_registry.component_loader import load_components_and_start_system

# Define a flag to control the main loop
keep_running = True


# Define signal handler to exit gracefully
def handle_exit_signal(signum, frame):
    global keep_running
    print("\nReceived exit signal. Shutting down...")
    keep_running = False
    # Stop all components that have a stop method
    from micro_registry.registry import instance_registry
    for component in instance_registry.values():
        if hasattr(component, 'stop'):
            component.stop()


# Register the signal handler
signal.signal(signal.SIGINT, handle_exit_signal)
signal.signal(signal.SIGTERM, handle_exit_signal)


def main():
    micro_registry.init()
    parser = argparse.ArgumentParser(description='Generic Application to load and start components from a YAML file.')
    parser.add_argument('-c', '--config', type=str, required=True, help='Path to the YAML configuration file.')
    parser.add_argument('-r', '--registry-directory', type=str, required=True, help='Path to the registry directory to load modules from.')
    args = parser.parse_args()

    # Load modules from the specified registry directory
    registry_directory = args.registry_directory
    if not os.path.isdir(registry_directory):
        print(f"Registry directory '{registry_directory}' not found.")
        sys.exit(1)

    # Add the registry directory to sys.path
    if registry_directory not in sys.path:
        sys.path.append(registry_directory)

    # Load modules from the registry directory
    load_modules_from_directory(registry_directory)

    # Optionally, load modules from the current directory
    current_script_directory = os.path.dirname(os.path.abspath(__file__))
    load_modules_from_directory(current_script_directory)

    # Load the components from the YAML configuration file
    config_file_path = args.config
    if not os.path.isfile(config_file_path):
        print(f"Configuration file '{config_file_path}' not found.")
        sys.exit(1)

    load_components_and_start_system(config_file_path)

    print("Application is running. Press Ctrl+C to stop.")

    # Keep the main program running
    while keep_running:
        time.sleep(1)

    print("Application has stopped.")


if __name__ == '__main__':
    main()
