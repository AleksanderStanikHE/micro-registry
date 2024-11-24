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
import threading
from concurrent.futures import ThreadPoolExecutor

from micro_registry.component import MicroComponent
from micro_registry.registry import register_class


@register_class
class Executor(MicroComponent):
    def __init__(self, name="", parent=None, **kwargs):
        super().__init__(name, parent)
        self.running = True
        self.loop = asyncio.new_event_loop()  # Custom event loop for Executor
        self.thread = threading.Thread(target=self.run_event_loop, daemon=True)
        self.default_interval = kwargs.get("default_interval", 1)
        self.child_last_run_times = {}  # Track last run times per child
        self.executor = (
            ThreadPoolExecutor()
        )  # Executor for synchronous child tasks if needed

    def run_event_loop(self):
        """Set up and run the custom event loop in a separate thread."""
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.run())
        except asyncio.CancelledError:
            pass  # Suppress the CancelledError exception
        except RuntimeError as e:
            if str(e) == "Event loop stopped before Future completed.":
                pass  # Suppress this specific exception
            else:
                self.logger.exception(f"Exception in run_event_loop: {e}")
        except Exception as e:
            # Optionally log other exceptions
            self.logger.exception(f"Exception in run_event_loop: {e}")
        # Do not close the loop here

    def start(self):
        """Start the event loop in a separate thread."""
        self.thread.start()

    async def run(self):
        """Periodically trigger the run methods of child components."""
        try:
            while self.running:
                tasks = []
                for child in self.children:
                    if hasattr(child, "run"):
                        interval = getattr(
                            child, "execution_interval", self.default_interval
                        )
                        last_run = self.child_last_run_times.get(child, None)
                        now = self.loop.time()
                        if last_run is None or now - last_run >= interval:
                            self.child_last_run_times[child] = now
                            if asyncio.iscoroutinefunction(child.run):
                                # If child's run method is asynchronous
                                tasks.append(asyncio.create_task(child.run()))
                            else:
                                # Run synchronous tasks in ThreadPoolExecutor
                                tasks.append(
                                    self.loop.run_in_executor(self.executor, child.run)
                                )
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    # Process exceptions to prevent warnings
                    for result in results:
                        if isinstance(result, Exception):
                            if isinstance(result, asyncio.CancelledError):
                                pass  # Expected due to cancellation
                            else:
                                # Optionally log other exceptions
                                self.logger.warning(f"Task exception: {result}")
                await asyncio.sleep(0.1)  # Main execution interval for Executor
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            pass

    def stop(self):
        """Stop the custom event loop and clean up resources."""
        self.running = False

        if self.thread.is_alive():
            # Cancel all pending tasks
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()

            # Allow the loop to process the cancellation
            if self.loop.is_running():
                self.loop.call_soon_threadsafe(self.loop.stop)

            self.thread.join()

        # Shutdown the executor and close the event loop
        self.executor.shutdown(wait=True)
        if not self.loop.is_closed():
            self.loop.close()
