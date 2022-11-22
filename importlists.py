# (c) 2022 lopho


stable_diffusion_v1 = [
    'collections.OrderedDict',
    'torch._utils._rebuild_tensor_v2',
    'torch.HalfStorage',
    'torch.FloatStorage',
    'torch.IntStorage',
    'torch.LongStorage',
    'pytorch_lightning.callbacks.model_checkpoint.ModelCheckpoint',
    'numpy.core.multiarray.scalar',
    'numpy.dtype',
    '_codecs.encode'
]


whitelists = { 'stable_diffusion_v1': stable_diffusion_v1 }

