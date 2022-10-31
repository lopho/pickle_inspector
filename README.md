# pickle_inspector 🥒🔬
Check what is in the pickle before eating it.

```py
import torch
import pickle_inspector
stubs = torch.load('sus.pt', pickle_module=pickle_inspector.pickle)
```
Outputs:
```
very_suspicious_function
torch._utils._rebuild_tensor_v2
collections.OrderedDict
numpy.core.multiarray.scalar
set_font_to_windings
numpy.dtype
_codecs.encode
```
