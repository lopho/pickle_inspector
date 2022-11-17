# (c) 2022 lopho
import pickle as python_pickle
from types import ModuleType
from functools import partial


def _check_list(what, where):
    for s in where:
        if s == what or (s.endswith('*') and what.startswith(s[:-1])):
            return True
    return False


class InspectorResult:
    def __init__(self):
        self.classes = []
        self.calls = []
        self.structure = {}


class UnpickleConfig:
    def __init__(self, blacklist = [], whitelist = []):
        self.blacklist = blacklist
        self.whitelist = whitelist
        self.verbose = True
        self.strict = False


class StubMeta:
    def __init__(self, module, name, result, config):
        self.module = module
        self.name = name
        self.full_name = f'{module}.{name}'
        self.args = {}
        self.kwargs = {}
        self.config = config
        self.result = result

    def _call_tracer(self, attr, *args, **kwargs):
        if attr not in self.args:
            self.args[attr] = []
            self.kwargs[attr] = []
        self.args[attr].append(args)
        self.kwargs[attr].append(kwargs)
        self.result.calls.append(f'{self.full_name}.{attr}({args}, {kwargs})')

    def __repr__(self):
        if '__call__' in self.args and len(self.args['__call__']) > 0:
            return f'{self.full_name}({self.args["__call__"][0]}, {self.kwargs["__call__"][0]})'
        else:
            return f'{self.full_name}()'

    def __call__(self, *args, **kwargs):
        self._call_tracer('__call__', *args, **kwargs)
        return self

    def __getattr__(self, attr):
        return partial(self._call_tracer, attr)

    def __setitem__(self, *args, **kwargs):
        self._call_tracer('__setitem__', *args, **kwargs)


class UnpickleBase(python_pickle.Unpickler):
    config = UnpickleConfig()
    def _print(self, *_):
        if self.config.verbose:
            print(*_)


class UnpickleInspector(UnpickleBase):
    def find_class(self, result, module, name):
        full_name = f'{module}.{name}'
        self._print(f'STUBBED {full_name}')
        result.classes.append(full_name)
        config = self.config
        return StubMeta(module, name, result, config)

    def load(self):
        result = InspectorResult()
        self.persistent_load = lambda *_: None # torch
        self.find_class = partial(UnpickleInspector.find_class, self, result)
        result.structure = super().load()
        return result


class BlockedException(Exception):
    def __init__(self, msg):
        self.msg = msg


class UnpickleControlled(UnpickleBase):
    def find_class(self, result, module, name):
        full_name = f'{module}.{name}'
        in_blacklist = _check_list(full_name, self.config.blacklist)
        in_whitelist = _check_list(full_name, self.config.whitelist)
        if (in_blacklist and not in_whitelist) or (len(self.config.blacklist) < 1 and len(self.config.whitelist) > 0 and not in_whitelist):
            if self.config.strict:
                raise BlockedException(f'strict mode: {full_name} blocked')
            else:
                return UnpickleInspector.find_class(self, result, module, name)
        self._print(full_name)
        result.classes.append(full_name)
        return super().find_class(module, name)

    def load(self):
        result = InspectorResult()
        self.find_class = partial(UnpickleControlled.find_class, self, result)
        result.structure = super().load()
        return result

class PickleModule(ModuleType):
    def __init__(self, unpickler, conf = UnpickleConfig()):
        super().__init__('pickle')
        class ConfiguredUnpickler(unpickler):
            config = conf
        self.Unpickler = ConfiguredUnpickler

inspector = PickleModule(UnpickleInspector)

