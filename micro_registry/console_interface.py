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

import asyncio
import atexit
import os
import threading
from datetime import datetime, timedelta

import yaml

from micro_registry.component import MicroComponent
from micro_registry.registry import instance_registry, register_class


@register_class
class ConsoleInterface(MicroComponent):
    def __init__(self, name="", parent=None, **kwargs):
        super().__init__(name, parent)
        self.config_file = kwargs.get("config_file", "console_interface.yaml")
        self.ui_config = kwargs.get("ui", None)
        self.running = True
        self.interface_config = {}
        self.load_config()
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_event_loop, daemon=True)
        self.thread.start()
        atexit.register(self.stop)

    def load_config(self):
        """Loads the interface configuration from the 'ui' parameter or a YAML file."""
        if self.ui_config:
            self.interface_config = self.ui_config
        else:
            try:
                with open(self.config_file, "r") as file:
                    self.interface_config = yaml.safe_load(file)
            except FileNotFoundError:
                print(f"Configuration file {self.config_file} not found.")
            except yaml.YAMLError as e:
                print(f"Error parsing YAML file: {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

    def run_event_loop(self):
        """Runs the event loop in a separate thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.run())
        self.loop.run_forever()

    async def run(self):
        """Main loop that updates the console display."""
        while self.running:
            self.display_interface()
            await asyncio.sleep(1)  # Adjust the refresh rate as needed

    def display_interface(self):
        """Displays the interface based on the configuration."""
        # Hide the cursor
        print("\033[?25l", end="")  # Hide the cursor

        # Clear the console
        os.system("cls" if os.name == "nt" else "clear")

        if not self.interface_config:
            print("No interface configuration loaded.")
            return

        display_items = self.interface_config.get("display_items", [])

        for item in display_items:
            item_type = item.get("type", "label")

            if item_type == "separator":
                self.display_separator(item)
            elif item_type == "groupbox":
                self.display_groupbox(item)
            elif item_type == "label":
                self.display_label(item)
            else:
                print(f"Unknown display item type: {item_type}")

        # Move the cursor to the bottom after drawing
        self.move_cursor_to_bottom()

        # Show the cursor
        print("\033[?25h", end="")  # Show the cursor

    def display_separator(self, item):
        """Displays a separator line."""
        line = item.get("line", 1)
        column = item.get("column", 1)
        character = item.get("character", "-")
        length = item.get("length", 50)

        text = character * length
        self.print_at_position(line, column, text)

    def display_groupbox(self, item):
        """Displays a group box with borders and a title."""
        line = item.get("line", 1)
        column = item.get("column", 1)
        title = item.get("title", "Group Box")
        width = item.get("width", 50)
        height = item.get("height", 5)

        # Define box drawing characters
        tl_corner = "+"
        tr_corner = "+"
        bl_corner = "+"
        br_corner = "+"
        horizontal = "-"
        vertical = "|"

        # Calculate the side lengths for the top border
        title_length = len(title) + 2  # Adding spaces around the title
        side_length = (width - title_length - 2) // 2
        extra_space = (width - title_length - 2) % 2  # For odd widths

        # Top border with title
        top_border = (
            f"{tl_corner}"
            f"{horizontal * side_length}"
            f" {title} "
            f"{horizontal * (side_length + extra_space)}"
            f"{tr_corner}"
        )
        self.print_at_position(line, column, top_border)

        # Middle empty lines with vertical borders
        for i in range(1, height - 1):
            empty_line = f"{vertical}{' ' * (width - 2)}{vertical}"
            self.print_at_position(line + i, column, empty_line)

        # Bottom border
        bottom_border = f"{bl_corner}{horizontal * (width - 2)}{br_corner}"
        self.print_at_position(line + height - 1, column, bottom_border)

    def display_label(self, item):
        """Displays a label with its corresponding component attribute."""
        label = item.get("label", "")
        component_name = item.get("component")
        attribute_name = item.get("attribute")
        line = item.get("line", 1)
        column = item.get("column", 1)

        component = instance_registry.get(component_name)
        if component is None:
            value = "Component not found"
        else:
            value = getattr(component, attribute_name, "Attribute not found")

        # Format datetime and timedelta objects
        if isinstance(value, datetime):
            value = value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(value, timedelta):
            # Format timedelta to HH:MM:SS
            total_seconds = int(value.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            value = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            value = str(value)

        # Prepare the text to display
        text = f"{label}: {value}"

        # Print at the specified position
        self.print_at_position(line, column, text)

    def print_at_position(self, line, column, text):
        """Prints text at the specified cursor position."""
        # ANSI escape code to move cursor
        move_cursor = f"\033[{line};{column}H"
        # Print without adding a new line
        print(f"{move_cursor}{text}", end="", flush=True)

    def move_cursor_to_bottom(self):
        """Moves the cursor to the bottom of the interface to avoid overwriting."""
        total_lines = self.calculate_total_lines()
        move_cursor = f"\033[{total_lines + 1};0H"
        print(move_cursor, end="")

    def calculate_total_lines(self):
        """Calculates the total number of lines used by the interface."""
        max_line = 0
        display_items = self.interface_config.get("display_items", [])
        for item in display_items:
            item_line = item.get("line", 1)
            if item.get("type") == "groupbox":
                height = item.get("height", 5)
                item_line += height - 1
            elif item.get("type") == "separator":
                pass  # Separators are single lines
            else:
                pass  # Labels are on a single line
            if item_line > max_line:
                max_line = item_line
        return max_line

    def stop(self):
        """Stops the component."""
        self.running = False
        # Show the cursor before exiting
        print("\033[?25h", end="")  # Show the cursor
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()
