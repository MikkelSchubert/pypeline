#!/usr/bin/python3
#
# Copyright (c) 2013 Mikkel Schubert <MikkelSch@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
import os
import multiprocessing

import paleomix
import paleomix.common.logging

from paleomix.common.argparse import ArgumentParser

_DEFAULT_CONFIG_FILES = [
    "/etc/paleomix/phylo_pipeline.ini",
    "~/.paleomix/phylo_pipeline.ini",
]


def build_parser():
    parser = ArgumentParser(
        prog="paleomix phylo_pipeline", default_config_files=_DEFAULT_CONFIG_FILES,
    )
    parser.add_argument(
        "commands",
        help="One or more commands separated by '+'. Available commands are 'help', to "
        "display this message; 'example', to create an example project; 'makefile', to "
        "print a makefile template; 'genotype' to perform genotyping on a makefile; "
        "'msa' to perform multiple sequence alignment on a makefile; and 'phylogeny', "
        "to carry out phylogenetic inference on a makefile.",
    )
    parser.add_argument("files", nargs="*", help="One or more YAML files")

    parser.add_argument(
        "--version", action="version", version="%(prog)s v" + paleomix.__version__,
    )

    paleomix.common.logging.add_argument_group(parser, default="info")

    group = parser.add_argument_group("Scheduling")
    group.add_argument(
        "--examl-max-threads",
        default=1,
        type=int,
        help="Maximum number of threads for each instance of ExaML [%(default)s]",
    )
    group.add_argument(
        "--max-threads",
        type=int,
        default=max(2, multiprocessing.cpu_count()),
        help="Max number of threads to use in total [%(default)s]",
    )
    group.add_argument(
        "--dry-run",
        default=False,
        action="store_true",
        help="If passed, only a dry-run in performed, the dependency tree is printed, "
        "and no tasks are executed.",
    )

    group = parser.add_argument_group("Required paths")
    group.add_argument(
        "--temp-root",
        default="./temp",
        type=os.path.abspath,
        help="Location for temporary files and folders [%(default)s]",
    )
    group.add_argument(
        "--samples-root",
        default="./data/samples",
        help="Location of BAM files for each sample [%(default)s]",
    )
    group.add_argument(
        "--regions-root",
        default="./data/regions",
        help="Location of BED files containing regions of interest [%(default)s]",
    )
    group.add_argument(
        "--prefix-root",
        default="./data/prefixes",
        help="Location of prefixes (FASTAs) [%(default)s]",
    )
    group.add_argument(
        "--refseq-root",
        default="./data/refseqs",
        help="Location of reference sequences (FASTAs) [%(default)s]",
    )
    group.add_argument(
        "--destination",
        default="./results",
        help="The destination folder for result files [%(default)s]",
    )

    group = parser.add_argument_group("Files and executables")
    group.add_argument(
        "--list-input-files",
        action="store_true",
        default=False,
        help="List all input files used by pipeline for the "
        "makefile(s), excluding any generated by the "
        "pipeline itself.",
    )
    group.add_argument(
        "--list-output-files",
        action="store_true",
        default=False,
        help="List all output files generated by pipeline for " "the makefile(s).",
    )
    group.add_argument(
        "--list-executables",
        action="store_true",
        default=False,
        help="List all executables required by the pipeline, "
        "with version requirements (if any).",
    )

    return parser
