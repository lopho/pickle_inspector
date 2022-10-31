import pickle as python_pickle
from types import ModuleType

class Stub:
    def __setstate__(self, *p):
        self.payload_state = p
    def __init__(self, *p):
        self.payload_init = p
        self.payload_state = ()

class UnpickleInspector(python_pickle.Unpickler):
    def find_class(self, module, name):
        print(f'{module}.{name}')
        return Stub

class PickleModule(ModuleType):
    Unpickler = UnpickleInspector

pickle = PickleModule('pickle')
