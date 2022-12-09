# Copyright (C) 2022  Lopho <contact@lopho.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pickletools
import pickle as python_pickle
from types import ModuleType
from functools import partial


def _check_list(what, where):
    for s in where:
        if s == what or (s.endswith('*') and what.startswith(s[:-1])):
            return True
    return False

def is_pickle(bytes_like):
    bytes_like.seek(0)
    ret = _is_pickle(bytes_like)
    bytes_like.seek(0)
    return ret

def _is_pickle(bytes_like):
    ops = pickletools.genops(bytes_like.read())
    opcodes = []
    try:
        for i,o in enumerate(ops):
            if i == 0:
                if o[0].name != 'PROTO':
                    return False
                if o[1] > 5:
                    return False
            opcodes.append(o[0])
    except ValueError:
        return False
    if len(opcodes) < 2:
        return False
    if opcodes[-1].name == 'STOP':
        return True
    return False


class InspectorResult:
    def __init__(self):
        self.imports = []
        self.calls = []
        self.flagged = []
        self.structure = {}


class UnpickleConfig:
    def __init__(
            self, blacklist = [],
            whitelist = [],
            verbose = True,
            strict = False,
            ignore_missing_imports = False
    ):
        self.blacklist = blacklist
        self.whitelist = whitelist
        self.verbose = verbose
        self.strict = strict
        self.ignore_missing_imports = ignore_missing_imports


class StubMeta:
    def __init__(self, module, name, result, config, flagged = False):
        self.module = module
        self.name = name
        self.full_name = f'{module}.{name}'
        self.args = {}
        self.kwargs = {}
        self.config = config
        self.result = result
        self.flagged = flagged

    def _call_tracer(self, attr, *args, **kwargs):
        if attr not in self.args:
            self.args[attr] = []
            self.kwargs[attr] = []
        self.args[attr].append(args)
        self.kwargs[attr].append(kwargs)
        callstr = f'{self.full_name}.{attr}({args}, {kwargs})'
        self.result.calls.append(callstr)
        if self.flagged:
            self.result.flagged.append(callstr)

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
        self._print(f'found: {full_name}')
        result.imports.append(full_name)
        config = self.config
        flagged = False
        in_blacklist = _check_list(full_name, self.config.blacklist)
        in_whitelist = _check_list(full_name, self.config.whitelist)
        if (in_blacklist and not in_whitelist) or (len(self.config.blacklist) < 1 and len(self.config.whitelist) > 0 and not in_whitelist):
            if self.config.strict:
                raise BlockedException(full_name)
            else:
                flagged = True
        return StubMeta(module, name, result, config, flagged)

    def load(self):
        result = InspectorResult()
        self.persistent_load = lambda *_: None # torch loads tensor values with persistent load, not needed when inspecting
        self.find_class = partial(UnpickleInspector.find_class, self, result) # torch subclasses passed-in unpickler with different find_class
        result.structure = super().load()
        return result


class BlockedException(Exception):
    def __init__(self, msg):
        super().__init__(f'BLOCKED: {msg}')


class UnpickleControlled(UnpickleBase):
    def find_class(self, result, module, name):
        full_name = f'{module}.{name}'
        in_blacklist = _check_list(full_name, self.config.blacklist)
        in_whitelist = _check_list(full_name, self.config.whitelist)
        if (in_blacklist and not in_whitelist) or (len(self.config.blacklist) < 1 and len(self.config.whitelist) > 0 and not in_whitelist):
            if self.config.strict:
                raise BlockedException(full_name)
            else:
                return UnpickleInspector.find_class(self, result, module, name)
        self._print('import:', full_name)
        result.imports.append(full_name)
        if self.config.ignore_missing_imports:
            try:
                super().find_class(module, name)
            except ImportError as e:
                self._print('ignore:', e)
                return None
        else:
            return super().find_class(module, name)

    def load(self):
        result = InspectorResult()
        self.find_class = partial(UnpickleControlled.find_class, self, result)
        result.structure = super().load()
        result.flags = getattr(self, 'config').flags
        return result


class PickleModule(ModuleType):
    def __init__(self, unpickler, conf = UnpickleConfig()):
        super().__init__('pickle')
        class ConfiguredUnpickler(unpickler):
            config = conf
        self.Unpickler = ConfiguredUnpickler


inspector = PickleModule(UnpickleInspector)

