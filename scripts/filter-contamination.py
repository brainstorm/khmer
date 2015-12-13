#! /usr/bin/env python2
#
# This file is part of khmer, http://github.com/ged-lab/khmer/, and is
# Copyright (C) Michigan State University, 2009-2014. It is licensed under
# the three-clause BSD license; see doc/LICENSE.txt.
# Contact: khmer-project@idyll.org
#
# pylint: disable=invalid-name,missing-docstring
"""
Screen for contamination in a similar way as FACS, fastq_screen or deconseq do.
The output is in JSON format by default, simplifying parsing/piping for third
party programs and pipelines, ie:

{"sample": ["sample.fastq"], "filter": "eschColi_K12.pt", "contamination": 0.3}

Usage:
% python scripts/filter-contamination.py <nodegraph> <data1> [ <data2> <...> ]

Use '-h' for parameter help.
"""
from __future__ import division


import khmer
import json
from collections import defaultdict
import argparse

from khmer.khmer_args import info
from khmer.kfile import check_input_files, check_space


def get_parser():
    epilog = """
    Example:


    load-graph.py --unique-kmers 200000 --fp-rate 0.05 --no-build-tagset \
            test-reads.oxling tests/test-data/test-reads.fa
    filter-contamination.py test-reads.oxling tests/test-reads/100-reads.fq.gz

    """
    parser = argparse.ArgumentParser(
        description="Determine which organisms are present in a given file ",
        epilog=epilog,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        'graph', help="path of the input k-mer nodegraph")
    parser.add_argument('data', help="files to be decontaminated")
    parser.add_argument('--version', action='version', version='%(prog)s '
                        + khmer.__version__)
    return parser

# http://scipher.wordpress.com/2010/12/02/simple-sliding-window-iterator-in-python/


def sliding_window_it(sequence, winSize):
    """Returns a generator that will iterate through
    the defined chunks of input sequence.  Input sequence
    must be iterable."""

    # Pre-compute number of chunks to emit
    numOfChunks = len(sequence) - winSize + 1

    # Do the work
    for i in range(0, numOfChunks):
        yield sequence[i:i + winSize]


def is_valid_dna(sequence):
    a_count = c_count = t_count = g_count = 0
    a_count = sequence.count('A') + sequence.count('a')
    c_count = sequence.count('C') + sequence.count('c')
    t_count = sequence.count('T') + sequence.count('t')
    g_count = sequence.count('G') + sequence.count('g')

    total_count = a_count + c_count + t_count + g_count

    if total_count != len(sequence):
        return False
    else:
        return True


def main():
    info('filter-contamination.py', ['graph', 'classification'])
    args = get_parser().parse_args()
    graph = args.graph
    data = args.data

    results = defaultdict(dict)

    # Get samples to be analyzed against the graph file
    filenames = [data]
    for _ in filenames:
        check_input_files(_, False)

    # Is there enough disk space available for input/output files before doing
    # anything?
    check_space(filenames, False)

    print 'loading nodegraph %s' % graph
    htable = khmer.load_nodegraph(graph)
    ksize = htable.ksize()

    for _, filename in enumerate(filenames):
        print('querying sample {sample} against filter {filt}').format(
            sample=filename, filt=graph)
        total_query_kmers = 0
        contaminant_total_matches = 0

        rparser = khmer.ReadParser(filename)

        for r in rparser:
            read_kmers = len(r.sequence) - ksize + 1
            if read_kmers == 0 or not is_valid_dna(r.sequence):
                continue
            contaminant_read_matches = 0

            for kmer in sliding_window_it(r.sequence, ksize):
                contaminant_read_matches += htable.get(kmer)

            contaminant_total_matches += contaminant_read_matches
            total_query_kmers += read_kmers

        contam = contaminant_total_matches / total_query_kmers

        results['sample'] = filenames
        results['filter'] = graph
        results['contamination'] = contam

        print json.dumps(results)

if __name__ == '__main__':
    main()

# vim: set ft=python ts=4 sts=4 sw=4 et tw=79:
