import pickle as python_pickle

class Stub:
    def __setstate__(*_): pass
    def __init__(*_): pass

class UnpickleInspector(python_pickle.Unpickler):
    def find_class(self, module, name):
        print(f'{module}.{name}')
        return Stub

class PickleModule(ModuleType):
    Unpickler = UnpickleInspector

pickle = PickleModule('pickle')
