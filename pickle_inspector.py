
import pickle as python_pickle
from types import ModuleType
from functools import partial


class InspectorResult:
    def __init__(self):
        self.calls = []
        self.structure = {}


class UnpickleInspector(python_pickle.Unpickler):
    def find_class(self, calls, module, name):
        print(f'{module}.{name}')
        class Stub:
            def __init__(self, *args, **kwargs):
                self.module = module
                self.name = name
                self.init_args = args
                self.init_kwargs = kwargs
                self.state_args = ()
                self.state_kwargs = {}
                calls.append(f'{module}.{name}({args}, {kwargs})')
            def __setstate__(self, *args, **kwargs):
                self.state_args = args
                self.state_kwargs = kwargs
                calls.append(f'{module}.{name}.__setstate__({args}, {kwargs})')
            def __repr__(self):
                return f'{self.module}.{self.name}({self.init_args}, {self.init_kwargs})'
        return Stub

    def persistent_load(*_):
        pass

    def load(self):
        result = InspectorResult()
        self.find_class = partial(UnpickleInspector.find_class, self, result.calls)
        result.structure = super().load()
        return result


class PickleModule(ModuleType):
    Unpickler = UnpickleInspector


pickle = PickleModule('pickle')

