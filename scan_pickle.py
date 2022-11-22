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

import io
import zipfile
from pickle_inspector import (
        is_pickle,
        UnpickleConfig,
        UnpickleInspector,
        PickleModule,
        BlockedException,
        importlists
)


def scan(path, pickle_module):
    print(f"Reading {path}")
    data = dict()
    if zipfile.is_zipfile(path):
        zf = zipfile.ZipFile(path)
        for f in zf.filelist:
            d = io.BytesIO(zf.read(f))
            if is_pickle(d):
                print(f"Found pickle in zip: {f.filename}")
                data[f.filename] = d
    else:
        with open(path, 'rb') as f:
            if is_pickle(f):
                data = { path: io.BytesIO(f.read()) }
    passed = True
    if len(data) < 1:
        print("No valid pickle found!")
        passed = False
    else:
        for k in data:
            print(f"Scanning: {k}")
            try:
                pickle_module.Unpickler(data[k]).load()
            except BlockedException as e:
                print(e)
                passed = False
    print("Scan for", path, "PASSED ✅" if passed else "FAILED! ⚠️")
    return passed


def main(args):
    from argparse import ArgumentParser
    from functools import partial
    print("Pickle Inspector")
    print("Copyright (C) 2022 Lopho <contact@lopho.org> | Licensed under AGPLv3 <https://www.gnu.org/licenses/agpl-3.0.html>")
    parser = ArgumentParser(
            description = "Scan pickles",
    )
    parser.add_argument(
        '-i', '--in',
        type = str,
        required = True,
        nargs = '+',
        dest = 'input',
        help = "path to a pickle(s) or zip(s) containing pickles"
    )
    parser.add_argument(
        '-p', '--preset',
        type = str,
        choices = importlists.whitelists.keys(),
        help = "a whitelist preset to use: stable_diffusion_v1"
    )
    parser.add_argument(
        '-w', '--whitelist',
        type = str,
        nargs = '+',
        help = "whitelist of modules and functions to allow"
    )
    parser.add_argument(
        '-b', '--blacklist',
        type = str,
        nargs = '+',
        help = "blacklist of modules and functions to block"
    )
    def error(self, message):
        import sys
        sys.stderr.write(f"error: {message}\n")
        self.print_help()
        self.exit()
    parser.error = partial(error, parser) # type: ignore
    args = parser.parse_args(args)
    whitelist = []
    blacklist = []
    if args.preset is not None:
        whitelist = importlists.whitelists[args.preset]
    if args.whitelist is not None:
        whitelist += args.whitelist
    if args.blacklist is not None:
        blacklist += args.blacklist
    print(f"Scanning file(s): {args.input}")
    if len(whitelist) > 0:
        print(f"Using white list: {whitelist}")
    if len(blacklist) > 0:
        print(f"Using black list: {blacklist}")
    conf = UnpickleConfig(
        strict = True,
        verbose = True,
        whitelist = whitelist,
        blacklist = blacklist
    )
    stubPickle = PickleModule(UnpickleInspector, conf)
    passed = True
    for p in args.input:
        if not scan(p, stubPickle):
            passed = False
    return passed


if __name__ == '__main__':
    import sys
    sys.exit(0) if main(sys.argv[1:]) else sys.exit(1)

