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

import argparse
import os
import signal
import sys
import time
import traceback

# Import necessary modules
# import micro_registry
from micro_registry.component_loader import load_components_and_start_system

# sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))


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
        if hasattr(component, "stop"):
            component.stop()


# Register the signal handler
signal.signal(signal.SIGINT, handle_exit_signal)
signal.signal(signal.SIGTERM, handle_exit_signal)


def main():
    # Initialize the registry if necessary
    # micro_registry.init()  # Uncomment if needed

    parser = argparse.ArgumentParser(
        description="Generic Application to load and start components from a YAML file."
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        required=True,
        help="Path to the YAML configuration file.",
    )
    parser.add_argument(
        "-r",
        "--registry-directory",
        type=str,
        help="Optional path to the registry directory to load modules from.",
    )
    args = parser.parse_args()

    # Handle registry directory if provided
    if args.registry_directory:
        registry_directory = args.registry_directory
        if not os.path.isdir(registry_directory):
            print(f"Registry directory '{registry_directory}' not found.")
            sys.exit(1)

        # Add the registry directory and its parent to sys.path
        registry_directory = os.path.abspath(registry_directory)
        if registry_directory not in sys.path:
            sys.path.insert(0, registry_directory)

        parent_directory = os.path.dirname(registry_directory)
        if parent_directory not in sys.path:
            sys.path.insert(0, parent_directory)

    # Always add the current script directory to sys.path
    current_script_directory = os.path.dirname(os.path.abspath(__file__))
    if current_script_directory not in sys.path:
        sys.path.insert(0, current_script_directory)

    # Also add the current working directory to sys.path
    current_working_directory = os.getcwd()
    if current_working_directory not in sys.path:
        sys.path.insert(0, current_working_directory)

    # Add the directory of the configuration file to sys.path
    config_file_path = args.config
    if not os.path.isfile(config_file_path):
        print(f"Configuration file '{config_file_path}' not found.")
        sys.exit(1)

    config_directory = os.path.dirname(os.path.abspath(config_file_path))
    if config_directory not in sys.path:
        sys.path.insert(0, config_directory)

    # Load the components from the YAML configuration file
    load_components_and_start_system(config_file_path)

    print("Application is running. Press Ctrl+C to stop.")

    # Keep the main program running
    while keep_running:
        time.sleep(1)

    print("Application has stopped.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
