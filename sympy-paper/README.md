# SymPy Paper

This is the source repository for the paper:

**SymPy: symbolic computing in python**

This paper has been published in PeerJ Computer Science and can be found at
https://peerj.com/articles/cs-103/.

To cite this paper, please use

> Meurer A, Smith CP, Paprocki M, Čertík O, Kirpichev SB, Rocklin M, Kumar A,
Ivanov S, Moore JK, Singh S, Rathnayake T, Vig S, Granger BE, Muller RP,
Bonazzi F, Gupta H, Vats S, Johansson F, Pedregosa F, Curry MJ, Terrel AR,
Roučka Š, Saboo A, Fernando I, Kulal S, Cimrman R, Scopatz A. (2017) SymPy:
symbolic computing in Python. *PeerJ Computer Science* 3:e103
https://doi.org/10.7717/peerj-cs.103

Here is the BibTeX entry.

```
@article{10.7717/peerj-cs.103,
 title = {SymPy: symbolic computing in Python},
 author = {Meurer, Aaron and Smith, Christopher P. and Paprocki, Mateusz and \v{C}ert\'{i}k, Ond\v{r}ej and Kirpichev, Sergey B. and Rocklin, Matthew and Kumar, AMiT and Ivanov, Sergiu and Moore, Jason K. and Singh, Sartaj and Rathnayake, Thilina and Vig, Sean and Granger, Brian E. and Muller, Richard P. and Bonazzi, Francesco and Gupta, Harsh and Vats, Shivam and Johansson, Fredrik and Pedregosa, Fabian and Curry, Matthew J. and Terrel, Andy R. and Rou\v{c}ka, \v{S}t\v{e}p\'{a}n and Saboo, Ashutosh and Fernando, Isuru and Kulal, Sumith and Cimrman, Robert and Scopatz, Anthony},
 year = 2017,
 month = jan,
 keywords = {Python, Computer algebra system, Symbolics},
 abstract = {
            SymPy is an open source computer algebra system written in pure Python. It is built with a focus on extensibility and ease of use, through both interactive and programmatic applications. These characteristics have led SymPy to become a popular symbolic library for the scientific Python ecosystem. This paper presents the architecture of SymPy, a description of its features, and a discussion of select submodules. The supplementary material provide additional examples and further outline details of the architecture and features of SymPy.
         },
 volume = 3,
 pages = {e103},
 journal = {PeerJ Computer Science},
 issn = {2376-5992},
 url = {https://doi.org/10.7717/peerj-cs.103},
 doi = {10.7717/peerj-cs.103}
}
```

You may also download other citation formats at the above URL.

This repository contains or links to all of the information needed to reproduce
the results in the paper.

The latest rendered version of the PDF can be viewed via the Travis build:

[![Build Status](https://travis-ci.org/sympy/sympy-paper.svg?branch=master)](https://travis-ci.org/sympy/sympy-paper)

Latest pdf: [paper-master.pdf](https://github.com/isuruf-bot/sympy-paper/blob/pdfs/paper-master.pdf)

# Preprint

A [preprint](https://peerj.com/preprints/2083/) of this paper has been submitted to
PeerJ.

# Contributing

Join our chat room to discuss contributions:

[![Join the chat at https://gitter.im/sympy/sympy-paper](https://badges.gitter.im/sympy/sympy-paper.svg)](https://gitter.im/sympy/sympy-paper?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

# License

[![CCBY](https://i.creativecommons.org/l/by/4.0/80x15.png)](http://creativecommons.org/licenses/by/4.0)

[![license](https://img.shields.io/github/license/mashape/apistatus.svg?maxAge=2592000)]()

The contents of this repository are dual licensed under the [Creative Commons
Attribution 4.0 International
License](http://creativecommons.org/licenses/by/4.0) and the [MIT
License](https://opensource.org/licenses/MIT). See the `LICENSE` file for
details.

# LaTeX Build Instructions

Install a full LaTeX suite on your preferred operating system. To build the
PDF type

    make

in the source directory. This will produce `paper.pdf`, the main paper, and
`supplement.pdf`, the supplementary material.

Alternatively, you can use docker, see the instructions in our
[Dockerfile](https://github.com/sympy/sympy-paper/blob/master/Dockerfile).

You can test all the examples in the paper with

    make test

This requires that SymPy 1.0 (exactly) is installed.

# Authorship Criteria

We follow the ICMJE [criteria](http://www.icmje.org/recommendations/browse/roles-and-responsibilities/defining-the-role-of-authors-and-contributors.html#two)
for authorship:

1. Substantial contributions to the conception or design of the work; or the
   acquisition, analysis, or interpretation of data for the work; AND

2. Drafting the work or revising it critically for important intellectual
   content; AND

3. Final approval of the version to be published; AND

4. Agreement to be accountable for all aspects of the work in ensuring that
   questions related to the accuracy or integrity of any part of the work are
   appropriately investigated and resolved.

Anyone who satisfies and is willing to accept these responsibilities and
commitments is welcome to be an author on this publication.
