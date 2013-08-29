#!/usr/bin/python
#
# Copyright (c) 2012 Mikkel Schubert <MSchubert@snm.ku.dk>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
from __future__ import with_statement

import os
import copy

import pypeline.common.fileutils as fileutils

from pypeline.common.formats.msa import MSA
from pypeline.node import Node, MetaNode
from pypeline.common.formats.fasta import FASTA
from pypeline.common.utilities import fragment



class CollectSequencesNode(Node):
    def __init__(self, fasta_files, sequences, destination, dependencies = ()):
        """
        fasta_files -- { taxon_name_1 : filename_1, ... }
        sequences   -- { interval_name_1, ... }
        """

        self._infiles     = copy.deepcopy(fasta_files)
        self._sequences   = copy.deepcopy(sequences)
        self._destination = copy.copy(destination)
        self._outfiles    = [os.path.join(destination, name + ".fasta") for name in self._sequences]

        Node.__init__(self,
                      description  = "<CollectSequences: %i sequences from %i files -> '%s'>" \
                            % (len(self._sequences), len(self._infiles), self._destination),
                      input_files  = self._infiles.values(),
                      output_files = self._outfiles,
                      dependencies = dependencies)


    def _run(self, _config, temp):
        fastas = {}
        for (name, filename) in self._infiles.iteritems():
            current_fastas = {}
            for record in FASTA.from_file(filename):
                current_fastas[record.name] = record.sequence
            fastas[name] = current_fastas
        fastas = list(sorted(fastas.items()))

        for sequence_name in sorted(self._sequences):
            lines = []
            for (taxon_name, sequences) in fastas:
                fastaseq = "\n".join(fragment(60, sequences[sequence_name]))
                lines.append(">%s\n%s\n" % (taxon_name, fastaseq))

            filename = os.path.join(temp, sequence_name + ".fasta")
            with open(filename, "w") as fasta:
                fasta.write("".join(lines))


    def _teardown(self, _config, temp):
        for sequence in self._sequences:
            filename = sequence + ".fasta"
            infile   = os.path.join(temp, filename)
            outfile  = os.path.join(self._destination, filename)

            fileutils.move_file(infile, outfile)


class FilterSingletonsNode(Node):
    def __init__(self, input_file, output_file, filter_by, dependencies):
        self._input_file      = input_file
        self._output_file     = output_file
        self._filter_by       = dict(filter_by)
        for (to_filter, groups) in self._filter_by.items():
            if not groups:
                raise RuntimeError("Singleton filtering must involve at least one taxa")
            self._filter_by[to_filter] = groups

        Node.__init__(self,
                      description  = "<FilterSingleton: '%s' -> '%s'>" \
                            % (input_file, output_file),
                      input_files  = [input_file],
                      output_files = [output_file],
                      dependencies = dependencies)

    def _run(self, _config, temp):
        alignment = MSA.from_file(self._input_file)
        for (to_filter, groups) in self._filter_by.iteritems():
            alignment = alignment.filter_singletons(to_filter, groups)

        temp_filename = fileutils.reroot_path(temp, self._output_file)
        with open(temp_filename, "w") as handle:
            alignment.to_file(handle)
        fileutils.move_file(temp_filename, self._output_file)




class FilterSingletonsMetaNode(MetaNode):
    def __init__(self, input_files, destination, filter_by, dependencies = ()):
        subnodes = []
        filter_by = dict(filter_by)
        for (filename, node) in input_files.iteritems():
            output_filename = fileutils.reroot_path(destination, filename)
            subnodes.append(FilterSingletonsNode(input_file   = filename,
                                                 output_file  = output_filename,
                                                 filter_by    = filter_by,
                                                 dependencies = node))

        MetaNode.__init__(self,
                          description  = "<FilterSingleton: %i files -> '%s'>" \
                            % (len(subnodes), destination),
                          subnodes     = subnodes,
                          dependencies = dependencies)
