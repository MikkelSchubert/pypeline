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
import os

from pypeline.common.utilities import safe_coerce_to_tuple
from pypeline.node import MetaNode
from pypeline.nodes.gatk import IndelRealignerNode
from pypeline.nodes.picard import MergeSamFilesNode
from pypeline.tools.bam_pipeline.nodes import IndexAndValidateBAMNode


class Prefix:
    def __init__(self, config, prefix, samples, features):
        self.name      = prefix["Name"]
        self.label     = prefix.get("Label") or self.name
        self.reference = prefix["Reference"]
        self.samples = safe_coerce_to_tuple(samples)
        self.bams    = {}
        self.folder  = config.destination
        self.target  = os.path.basename(self.samples[0].folder)

        files_and_nodes = {}
        for sample in self.samples:
            files_and_nodes.update(sample.bams.iteritems())

        if "Raw BAM" in features:
            self.bams.update(self._build_raw_bam(config, prefix, files_and_nodes))
        if "Realigned BAM" in features:
            self.bams.update(self._build_realigned_bam(config, prefix, files_and_nodes))

        sample_nodes = [sample.node for sample in self.samples]
        if not self.bams:
            self.bams = bams
            self.node = MetaNode(description  = "Prefix: %s" % prefix["Name"],
                                 dependencies = nodes)
            nodes     = sample_nodes
        else:
            self.node = MetaNode(description  = "Final BAMs: %s" % prefix["Name"],
                                 subnodes     = self.bams.values(),
                                 dependencies = sample_nodes)


    def _build_raw_bam(self, config, prefix, files_and_bams):
        output_filename = os.path.join(self.folder, "%s.%s.bam" % (self.target, prefix["Name"]))
        validated_filename = os.path.join(self.folder, self.target, prefix["Name"] + ".validated")

        node = MergeSamFilesNode(config       = config,
                                 input_bams   = files_and_bams.keys(),
                                 output_bam   = output_filename,
                                 dependencies = files_and_bams.values())
        validated_node = IndexAndValidateBAMNode(config, node, validated_filename)

        return {output_filename : validated_node}


    def _build_realigned_bam(self, config, prefix, bams):
        output_filename    = os.path.join(self.folder, "%s.%s.realigned.bam" % (self.target, prefix["Name"]))
        intervals_filename = os.path.join(self.folder, self.target, prefix["Name"] + ".intervals")
        validated_filename = os.path.join(self.folder, self.target, prefix["Name"] + ".realigned.validated")

        node = IndelRealignerNode(config       = config,
                                  reference    = prefix["Reference"],
                                  infiles      = bams.keys(),
                                  outfile      = output_filename,
                                  intervals    = intervals_filename,
                                  dependencies = bams.values())
        validated_node = IndexAndValidateBAMNode(config, node, validated_filename)

        return {output_filename : validated_node}