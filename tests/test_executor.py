# Filename: test_executor.py
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

import unittest
import asyncio
import threading
import time
import sys
import os
import logging
from concurrent.futures import ThreadPoolExecutor

# Add the parent directory to sys.path to import the micro_registry module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from micro_registry.component import MicroComponent
from micro_registry.executor import Executor  # Adjust this import based on your project structure

from unittest.mock import MagicMock


class TestExecutor(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.CRITICAL)
        """Set up resources before each test."""
        self.executors = []

    def tearDown(self):
        """Clean up resources after each test."""
        for executor in self.executors:
            executor.stop()
        # Reset the event loop policy to avoid interference between tests
        asyncio.set_event_loop_policy(None)

    def test_executor_initialization(self):
        """Test that the Executor initializes correctly."""
        executor = Executor(name='test_executor')
        self.executors.append(executor)
        self.assertTrue(executor.running)
        self.assertIsInstance(executor.loop, asyncio.AbstractEventLoop)
        self.assertIsInstance(executor.thread, threading.Thread)
        self.assertEqual(executor.default_interval, 1)
        self.assertEqual(executor.child_last_run_times, {})
        self.assertIsInstance(executor.executor, ThreadPoolExecutor)

    def test_executor_start_and_stop(self):
        """Test that the Executor starts and stops without errors."""
        executor = Executor(name='test_executor')
        self.executors.append(executor)
        executor.start()
        time.sleep(0.1)  # Allow time for the thread to start
        self.assertTrue(executor.thread.is_alive())
        executor.stop()
        self.assertFalse(executor.thread.is_alive())
        self.assertTrue(executor.loop.is_closed())

    def test_executor_runs_synchronous_child_run_methods(self):
        """Test that the Executor runs synchronous child components' run methods."""
        # Mock child component with a synchronous run method
        child = MagicMock(spec=MicroComponent)
        child.run = MagicMock()
        child.execution_interval = 0.1

        executor = Executor(name='test_executor')
        self.executors.append(executor)
        executor.children.append(child)

        executor.start()
        time.sleep(0.5)
        executor.stop()

        # The child's run method should be called multiple times
        self.assertGreaterEqual(child.run.call_count, 4)

    def test_executor_runs_asynchronous_child_run_methods(self):
        if sys.version_info >= (3, 8):
            from unittest.mock import AsyncMock
            """Test that the Executor runs asynchronous child components' run methods."""
            # Mock child component with an asynchronous run method
            child = MagicMock(spec=MicroComponent)
            child.run = AsyncMock()
            child.execution_interval = 0.1

            executor = Executor(name='test_executor')
            self.executors.append(executor)
            executor.children.append(child)

            executor.start()
            time.sleep(1.0)
            executor.stop()

            # The child's run method should be called multiple times
            self.assertGreaterEqual(child.run.call_count, 4)

    def test_executor_uses_default_interval(self):
        """Test that the Executor uses the default interval when no execution_interval is set."""
        # Mock child component without execution_interval
        child = MagicMock(spec=MicroComponent)
        child.run = MagicMock()

        executor = Executor(name='test_executor', default_interval=0.2)
        self.executors.append(executor)
        executor.children.append(child)

        executor.start()
        time.sleep(0.5)
        executor.stop()

        # The child's run method should be called at least twice
        self.assertGreaterEqual(child.run.call_count, 2)

    def test_executor_tracks_last_run_times(self):
        """Test that the Executor tracks the last run times of child components."""
        child = MagicMock(spec=MicroComponent)
        child.run = MagicMock()
        child.execution_interval = 0.1

        executor = Executor(name='test_executor')
        self.executors.append(executor)
        executor.children.append(child)

        executor.start()
        time.sleep(0.3)
        executor.stop()

        # Check that last run times are recorded
        self.assertIn(child, executor.child_last_run_times)
        last_run_time = executor.child_last_run_times[child]
        self.assertIsInstance(last_run_time, float)

    def test_executor_cleans_up_resources(self):
        """Test that the Executor cleans up resources upon stopping."""
        executor = Executor(name='test_executor')
        self.executors.append(executor)
        executor.start()
        time.sleep(0.1)
        executor.stop()
        self.assertFalse(executor.thread.is_alive())
        self.assertTrue(executor.executor._shutdown)
        self.assertTrue(executor.loop.is_closed())

    def test_executor_handles_no_children(self):
        """Test that the Executor handles the case when there are no child components."""
        executor = Executor(name='test_executor')
        self.executors.append(executor)
        executor.start()
        time.sleep(0.1)
        executor.stop()
        # No exceptions should occur

    def test_executor_handles_exception_in_child_run(self):
        """Test that the Executor handles exceptions in child run methods gracefully."""
        # Mock child component that raises an exception
        child = MagicMock(spec=MicroComponent)
        child.run = MagicMock(side_effect=Exception("Test exception"))
        child.execution_interval = 0.1

        executor = Executor(name='test_executor')
        self.executors.append(executor)
        executor.children.append(child)

        executor.start()
        time.sleep(0.2)
        executor.stop()

        # The child's run method should be called at least once
        self.assertGreaterEqual(child.run.call_count, 1)

    def test_executor_respects_individual_child_intervals(self):
        """Test that the Executor respects individual execution intervals for child components."""
        # Mock child components with different execution intervals
        child1 = MagicMock(spec=MicroComponent)
        child1.run = MagicMock()
        child1.execution_interval = 0.1

        child2 = MagicMock(spec=MicroComponent)
        child2.run = MagicMock()
        child2.execution_interval = 0.2

        executor = Executor(name='test_executor')
        self.executors.append(executor)
        executor.children.extend([child1, child2])

        executor.start()
        time.sleep(0.5)
        executor.stop()

        # child1's run method should be called more times than child2's
        self.assertGreater(child1.run.call_count, child2.run.call_count)

    def test_executor_stops_running_when_running_is_false(self):
        """Test that the Executor exits the run loop when self.running is set to False."""
        executor = Executor(name='test_executor')
        self.executors.append(executor)
        executor.start()
        time.sleep(0.1)
        executor.running = False
        executor.thread.join(timeout=1)
        self.assertFalse(executor.thread.is_alive())

    def test_executor_handles_asyncio_cancelled_error(self):
        """Test that the Executor handles asyncio.CancelledError without crashing."""
        executor = Executor(name='test_executor')
        self.executors.append(executor)

        # Replace the run method to raise asyncio.CancelledError
        async def cancelled_run():
            raise asyncio.CancelledError()

        executor.run = cancelled_run

        executor.start()
        time.sleep(0.1)
        executor.stop()
        # No exceptions should occur

    def test_executor_handles_event_loop_closure(self):
        """Test that the Executor does not produce warnings about unclosed event loops."""
        executor = Executor(name='test_executor')
        self.executors.append(executor)
        executor.start()
        time.sleep(0.1)
        executor.stop()

        # Check that the event loop is closed
        self.assertTrue(executor.loop.is_closed())


if __name__ == '__main__':
    unittest.main()
