# scheduler.py
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from micro_registry.registry import register_class
from micro_registry.component import MicroComponent
import sched
import time
from threading import Thread, Event
from automations import Automation


@register_class
class Scheduler(MicroComponent):
    def __init__(self, name: str, parent=None, **kwargs):
        super().__init__(name, parent)
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.thread_started = False  # Flag to track if the thread has been started
        self.stop_event = Event()  # Event to signal the thread to stop

    def prepare(self):
        super().prepare()
        print(f"Scheduler '{self.name}' is prepared.")

    def start(self):
        if not self.thread_started:
            print(f"Scheduler '{self.name}' is starting.")
            self.thread = Thread(target=self.run_scheduler)
            self.thread.daemon = True
            try:
                self.thread.start()
                self.thread_started = True
            except RuntimeError as e:
                print(f"Failed to start scheduler thread: {e}")
        else:
            print(f"Scheduler '{self.name}' is already running.")
        # super().start()

    def run_scheduler(self):
        print(f"Scheduler '{self.name}' thread is running.")
        while not self.stop_event.is_set():
            self.scheduler.run(blocking=False)
            time.sleep(0.1)  # Sleep briefly to prevent high CPU usage

    def schedule_automation(self, automation: Automation, delay_seconds: int):
        self.scheduler.enter(delay_seconds, 1, automation.execute, argument=())
        print(f"Automation '{automation.name}' scheduled to run in {delay_seconds} seconds.")

    def stop(self):
        print(f"Scheduler '{self.name}' is stopping.")
        self.stop_event.set()
        if self.thread_started and self.thread.is_alive():
            self.thread.join()
            self.thread_started = False
        super().stop()
