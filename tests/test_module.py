# test_module.py
class TestComponent:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent

    def prepare(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass
