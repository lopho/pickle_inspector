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


stable_diffusion_v2 = [
        'collections.OrderedDict',
        'torch._utils._rebuild_tensor_v2',
        'torch.HalfStorage',
        'torch.FloatStorage',
        'torch.IntStorage'
]

arbitrary_exec = [
        '__builtin__.exec', 'builtins.exec',
        '__builtin__.eval', 'builtins.eval',
        '__builtin__.open', 'builtins.open',
        '__builtin__.compile', 'builtins.compile',
        '__builtin__.breakpoint', 'builtins.breakpoint',
        '__builtin__.getattr', 'builtins.getattr'
        'subprocess.*',
        'requests.*',
        'httplib.*',
        'aiohttp.*',
        'webbrowser.*',
        'socket.*',
        'os.*',
        'nt.*',
        'posix.*',
        'sys.*'
]

blacklists = {
        'exec': arbitrary_exec
}

whitelists = {
        'stable_diffusion_v1': stable_diffusion_v1,
        'stable_diffusion_v2': stable_diffusion_v2
}

