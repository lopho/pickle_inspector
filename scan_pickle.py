# Copyright (C) 2023  Lopho <contact@lopho.org>
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
from enum import Enum
from pickle_inspector import (
        is_pickle,
        UnpickleConfig,
        UnpickleInspector,
        PickleModule,
        BlockedException,
        importlists
)


class ScanResult(Enum):
    PASSED = 0
    BLOCKED = 1
    FAILED = 2


def scan(path, pickle_module):
    flagged = []
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
    passed = ScanResult.PASSED
    if len(data) < 1:
        print("No valid pickle found!")
        passed = ScanResult.FAILED
    else:
        for k in data:
            print(f"Scanning: {k}")
            try:
                r = pickle_module.Unpickler(data[k]).load()
                if len(r.flagged) > 0:
                    passed = ScanResult.BLOCKED
                    flagged += r.flagged
            except BlockedException as e:
                print(e)
                passed = ScanResult.BLOCKED
    if passed is ScanResult.PASSED:
        print(f"\nScan for {path} PASSED ✅")
    else:
        print(f"\nFound blacklisted items:\n")
        for v in flagged:
            print(f'  {v}')
        print(f"\nScan for {path} FAILED ⚠️")
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
        default = [],
        nargs = '+',
        choices = importlists.whitelists.keys(),
        help = "a whitelist preset to use"
    )
    parser.add_argument(
        '-f', '--preset_blacklist',
        type = str,
        default = [],
        nargs = '+',
        choices = importlists.blacklists.keys(),
        help = "a blacklist preset to use"
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
    for preset in args.preset:
        print(f"Using preset: {preset}")
        whitelist += importlists.whitelists[preset]
    for preset in args.preset_blacklist:
        print(f"Using blacklist: {preset}")
        blacklist += importlists.blacklists[preset]
    if args.whitelist is not None:
        whitelist += args.whitelist
    if args.blacklist is not None:
        blacklist += args.blacklist
    blacklist = list(set(blacklist))
    whitelist = list(set(whitelist))
    print(f"Scanning file(s): {args.input}")
    if len(whitelist) > 0:
        print(f"Using white list: {whitelist}")
    if len(blacklist) > 0:
        print(f"Using black list: {blacklist}")
    conf = UnpickleConfig(
        strict = False,
        verbose = True,
        whitelist = whitelist,
        blacklist = blacklist
    )
    stubPickle = PickleModule(UnpickleInspector, conf)
    passed = ScanResult.PASSED
    for p in args.input:
        result = scan(p, stubPickle)
        if result is not ScanResult.PASSED:
            passed = result
    return passed


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]).value)

