#!/usr/bin/env xonsh
# -*- mode: python -*-
"""Diffs the latex file and builds the pdf."""
import os
import sys
from argparse import ArgumentParser

$RAISE_SUBPROC_ERROR = True

# Uncomment this for debugging

# trace on

def replace_inputs(diffname, files):
    with open(diffname, 'r') as fh:
        s = fh.read()
    for f in files:
        fbase, _ = os.path.splitext(f)
        s = s.replace('\\input{' + fbase + '}', '\\input{' + fbase + '-diff}')
        s = s.replace('\\input{' + f + '}', '\\input{' + fbase + '-diff}')
    with open(diffname, 'w') as fh:
        fh.write(s)


def difftex(old):
    files = set(`.*?\.tex`) - set(`.*?-diff\.tex`)
    files -= {
        'authors.tex',
        'coverletter.tex',
        'coverletter2.tex',
        'rebuttal.tex',
        'rebuttal2.tex',
        }
    new_files = set()
    for f in files:
        print('diffing ' + f)
        fbase, fext = os.path.splitext(f)
        oldspec = old + ':' + f
        oldname = '/tmp/{0}-{1}{2}'.format(fbase, old, fext)
        diffname = '{0}-diff{1}'.format(fbase, fext)
        if f in new_files:
            touch @(oldname)
        else:
            git show @(oldspec) > @(oldname)
        latexdiff -c "PICTUREENV=(?:picture|DIFnomarkup|lstlisting)[\w\d*@]*" @(oldname) @(f) > @(diffname)
        replace_inputs(diffname, files)

    cp authors.tex authors-diff.tex

    rm -rf /tmp/paper-diff
    git clone @(os.path.dirname($ARG0)) /tmp/paper-diff

    cwd = os.path.abspath(os.path.dirname($ARG0))
    cd /tmp/paper-diff
    git checkout @(old)
    make paper.pdf supplement.pdf
    cp /tmp/paper-diff/paper.bbl @(os.path.join(cwd, 'paper-' + old + '.bbl'))
    cp /tmp/paper-diff/supplement.bbl @(os.path.join(cwd, 'supplement-' + old + '.bbl'))
    cd @(cwd)

    latexdiff @(os.path.join(cwd, 'paper-' + old + '.bbl')) paper.bbl > paper-diff.bbl
    latexdiff @(os.path.join(cwd, 'supplement-' + old + '.bbl')) supplement.bbl > supplement-diff.bbl
    # latexdiff @(os.path.join(cwd, 'supplement' + '.bbl')) supplement.bbl > supplement-diff.bbl

def fixes():
    with open('comparison_with_mma-diff.tex') as f:
        text = f.read()
    with open('comparison_with_mma-diff.tex', 'w') as f:
        f.write(text.replace('\\PAR', ''))

    with open('supplement-diff.bbl') as f:
        text = f.read()
    with open('supplement-diff.bbl', 'w') as f:
        f.write(text.replace(r'\DIFdelbegin %DIFDELCMD < \bibitem[Abramowitz and Stegun, 1964]{Abramowitz1964handbook}',
r'''\DIFdelbegin %DIFDELCMD <
\bibitem[Abramowitz and Stegun, 1964]{Abramowitz1964handbook}'''))


def main(args=None):
    parser = ArgumentParser('diff')
    parser.add_argument('old', help='Tree to compare against.')
    parser.add_argument('--manuscript', help='Diffed manuscript name',
                        default='paper-diff.pdf', dest='manuscript')
    ns = parser.parse_args(args=args or $ARGS[1:])

    difftex(ns.old)
    fixes()

if __name__ == '__main__':
    main()
