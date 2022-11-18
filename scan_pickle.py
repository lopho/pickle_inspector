# (c) 2022 lopho
import sys
from argparse import ArgumentParser
import torch
from pickle_inspector import (
        UnpickleConfig,
        UnpickleInspector,
        PickleModule,
        BlockedException,
        whitelists
)

def main(args):
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
    args = parser.parse_args(args)
    print(args)
    whitelist = []
    blacklist = []
    if args.preset is not None:
        whitelist = whitelists.lists[args.preset]
    if args.whitelist is not None:
        whitelist += args.whitelist
    if args.blacklist is not None:
        blacklist += args.blacklist
    conf = UnpickleConfig(
        strict = True,
        verbose = True,
        whitelist = whitelist,
        blacklist = blacklist
    )
    pickle = PickleModule(UnpickleInspector, conf)
    passed = True
    try:
        torch.load(args.ckpt, pickle_module = pickle)
    except BlockedException as e:
        print(e)
        passed = False
    print("Scan", "PASSED ✅" if passed else "FAILED! ⚠️")
    return passed

if __name__ == '__main__':
    sys.exit(0) if main(sys.argv[1:]) else sys.exit(1)

