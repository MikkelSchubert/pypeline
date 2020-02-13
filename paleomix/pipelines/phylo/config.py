#!/usr/bin/python
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
import optparse
import sys

import paleomix
import paleomix.pipelines.phylo.parts.genotype as genotype
import paleomix.pipelines.phylo.parts.msa as msa
import paleomix.pipelines.phylo.parts.phylo as phylo

from paleomix.config import ConfigError, PerHostConfig, PerHostValue

_DESCRIPTION = (
    "Commands:\n"
    "  -- %prog help            -- Display this message.\n"
    "  -- %prog example [...]   -- Copy example project to folder.\n"
    "  -- %prog makefile        -- Print makefile template.\n"
    "  -- %prog genotype [...]  -- Carry out genotyping according to makefile.\n"
    "  -- %prog msa [...]       -- Carry out multiple sequence alignment.\n"
    "  -- %prog phylogeny [...] -- Carry out phylogenetic inference.\n"
)


_COMMANDS = {
    "mkfile": True,
    "makefile": True,
    "genotype": genotype.chain,
    "genotyping": genotype.chain,
    "msa": msa.chain,
    "phylogeny:examl": phylo.chain_examl,
}


class CustomHelpFormatter(optparse.IndentedHelpFormatter):
    def format_description(self, description):
        return description or ""


def select_commands(chain):
    commands = []
    for command in chain.split("+"):
        command_key = command.strip().lower()
        command_func = None

        if command in _COMMANDS:
            command_func = _COMMANDS[command_key]
        elif len(command) >= 3:
            for (key, value) in _COMMANDS.items():
                if key.startswith(command):
                    command_key = key
                    command_func = value
                    break

        commands.append((command_key, command_func))

    return commands


def _run_config_parser(argv):
    per_host_cfg = PerHostConfig("phylo_pipeline")
    usage_str = "paleomix phylo_pipeline <command> [options] [makefiles]"
    version_str = "paleomix phylo_pipeline v%s" % (paleomix.__version__,)
    parser = optparse.OptionParser(usage=usage_str, version=version_str)

    parser.formatter = CustomHelpFormatter()
    parser.formatter.set_parser(parser)
    parser.description = _DESCRIPTION

    paleomix.logger.add_optiongroup(parser, default=PerHostValue("warning"))

    group = optparse.OptionGroup(parser, "Scheduling")
    group.add_option(
        "--examl-max-threads",
        default=PerHostValue(1),
        type=int,
        help="Maximum number of threads to use for each instance of ExaML [%default]",
    )
    group.add_option(
        "--max-threads",
        default=per_host_cfg.max_threads,
        type=int,
        help="Maximum number of threads to use in total [%default]",
    )
    group.add_option(
        "--dry-run",
        default=False,
        action="store_true",
        help="If passed, only a dry-run in performed, the dependency tree is printed, "
        "and no tasks are executed.",
    )
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, "Required paths")
    group.add_option(
        "--temp-root",
        default=per_host_cfg.temp_root,
        help="Location for temporary files and folders [%default]",
    )
    group.add_option(
        "--samples-root",
        default=PerHostValue("./data/samples", is_path=True),
        help="Location of BAM files for each sample [%default]",
    )
    group.add_option(
        "--regions-root",
        default=PerHostValue("./data/regions", is_path=True),
        help="Location of BED files containing regions of interest [%default]",
    )
    group.add_option(
        "--prefix-root",
        default=PerHostValue("./data/prefixes", is_path=True),
        help="Location of prefixes (FASTAs) [%default]",
    )
    group.add_option(
        "--refseq-root",
        default=PerHostValue("./data/refseqs", is_path=True),
        help="Location of reference sequences (FASTAs) [%default]",
    )
    group.add_option(
        "--destination",
        default="./results",
        help="The destination folder for result files [%default]",
    )
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, "Files and executables")
    group.add_option(
        "--list-input-files",
        action="store_true",
        default=False,
        help="List all input files used by pipeline for the "
        "makefile(s), excluding any generated by the "
        "pipeline itself.",
    )
    group.add_option(
        "--list-output-files",
        action="store_true",
        default=False,
        help="List all output files generated by pipeline for " "the makefile(s).",
    )
    group.add_option(
        "--list-executables",
        action="store_true",
        default=False,
        help="List all executables required by the pipeline, "
        "with version requirements (if any).",
    )
    parser.add_option_group(group)

    return per_host_cfg.parse_args(parser, argv)


def parse_config(argv):
    options, args = _run_config_parser(argv)

    if args and args[0] in ("example", "examples"):
        return options, args
    elif (len(args) < 2) and (args != ["mkfile"] and args != ["makefile"]):
        description = _DESCRIPTION.replace("%prog", "phylo_pipeline").strip()
        print("Phylogeny Pipeline v%s\n" % (paleomix.__version__,), file=sys.stderr)
        print(description, file=sys.stderr)
        return options, args

    commands = select_commands(args[0] if args else ())
    if any((func is None) for (_, func) in commands):
        unknown_commands = ", ".join(
            repr(key) for (key, func) in commands if func is None
        )
        raise ConfigError("Unknown analysis step(s): %s" % (unknown_commands,))

    return options, args