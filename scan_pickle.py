# (c) 2022 lopho
from pickle_inspector import (
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
        '-c', '--ckpt',
        type = str,
        required = True,
        help = "path to a torch pickle"
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
    print(f"Using checkpoint: {args.ckpt}")
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
    pickle = PickleModule(UnpickleInspector, conf)
    import torch
    if torch.__version__.startswith('1.13.0'):
        print("WARNING: torch == 1.13.0 is not supported")
        print("Please install torch 1.12.1, 1.13.1 or later")
        return False
    passed = True
    try:
        torch.load(args.ckpt, pickle_module = pickle)
    except BlockedException as e:
        print(e)
        passed = False
    print("Scan", "PASSED ✅" if passed else "FAILED! ⚠️")
    return passed

if __name__ == '__main__':
    import sys
    sys.exit(0) if main(sys.argv[1:]) else sys.exit(1)

