import sys
import argparse
import logging
import os

logging_level = logging.CRITICAL

if os.environ.get('DEBUG'):
    logging_level = logging.DEBUG

logging.basicConfig(level=logging_level)
logger = logging.getLogger(__file__)

from transpiler import Transpiler

if __name__ == '__main__':
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument(
        '-i', '--input', type=str,
        help='Path to text file with program description in natural language')
    argument_parser.add_argument(
        '-o', '--output', type=str,
        help='Path of text file to write generated code',
        required=False, default=None
    )

    args = argument_parser.parse_args(sys.argv[1:])

    input_ = args.input
    logger.debug('input: {}'.format(input_))

    with open(input_, 'r') as fhandle:
        text = fhandle.read()

    transpiler = Transpiler()
    code = transpiler.transpile(text)

    if args.output:
        with open(args.output, 'w') as fhandle:
            fhandle.write(code)
    else:
        print(code)
