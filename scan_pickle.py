# (c) 2022 lopho

import io
import zipfile
from pickle_inspector import (
        is_pickle,
        UnpickleConfig,
        UnpickleInspector,
        PickleModule,
        BlockedException,
        whitelists
)


def main(args):
    from argparse import ArgumentParser
    from functools import partial
    parser = ArgumentParser("Scan pickles")
    parser.add_argument(
        '-i', '--in',
        type = str,
        required = True,
        dest = 'input',
        help = "path to a pickle or a zip containing pickles"
    )
    parser.add_argument(
        '-p', '--preset',
        type = str,
        choices = whitelists.lists.keys(),
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
        whitelist = whitelists.lists[args.preset]
    if args.whitelist is not None:
        whitelist += args.whitelist
    if args.blacklist is not None:
        blacklist += args.blacklist
    print(f"Scanning file: {args.input}")
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
    data = dict()
    if zipfile.is_zipfile(args.input):
        zf = zipfile.ZipFile(args.input)
        for f in zf.filelist:
            data[f.filename] = io.BytesIO(zf.read(f))
    else:
        with open(args.input, 'rb') as f:
            data = { args.input: io.BytesIO(f.read()) }
    passed = True
    for k in [ k for k in data if is_pickle(data[k]) ]:
        data[k].seek(0)
        try:
            stubPickle.Unpickler(data[k]).load()
        except BlockedException as e:
            print(e)
            passed = False
    print("Scan", "PASSED ✅" if passed else "FAILED! ⚠️")


if __name__ == '__main__':
    import sys
    sys.exit(0) if main(sys.argv[1:]) else sys.exit(1)

