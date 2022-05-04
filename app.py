#!/usr/bin/env python3
import argparse
from subprocess import Popen
import os
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage='%(prog)s [options]')
    parser.add_argument("-f", type = str, required = True, help="target file")
    parser.add_argument("-i", type = str, choices = ["yes", "no"],
                        default = "no", help="enable interactive debugging")
    parser.add_argument("-w", type = str, default = "no", choices = ["yes", "no"], help="launch web frontend")
    parser.add_argument("-d", type = str, required = True, 
                        choices = ["single-stepping", "top-down", "heaviest-first", "divide-and-query"],
                        help="debugging strategy")
    parser.add_argument("-pr", type = str, required = True, 
                        choices = ["bus", "bfs", "iddfs"],
                        help="program repair strategy")
    parser.add_argument("-t", type = str, default = "trace.dat", help = "trace log")
    parser.add_argument("-c", type = str, default = "coverage.dat", help="static coverage file")

    args = parser.parse_args()
    if args.w == "yes":
        if args.i == "no":
            from server import WSHandler, run_server
            _pydd = "./pydd.py"
            _args = f"-f {args.f} -i {args.i} -w {args.w} -d {args.d} -pr {args.pr} -t {args.t} -c {args.c}"
            setattr(WSHandler, "pydd", _pydd)
            setattr(WSHandler, "args", _args)
            try:
                Popen("cd frontend; npm start &", shell = True).wait()
                run_server()
            except (KeyboardInterrupt, SystemExit):
                print("\nExiting now.", flush=True)
        else:
            print("Interactive mode not currently supported.", file=sys.stderr)
            exit(-1)
    else:
        from pydd import PyDD
        with PyDD(args.f, args.i, args.w, args.d, args.pr, (args.t, args.c)) as debugger:
            debugger.run()
            try:
                debugger.start_debugging()
            except (KeyboardInterrupt, SystemExit):
                print("\nExiting now.", flush=True)