[![Build Status](https://travis-ci.org/flu-crew/smot.svg?branch=master)](https://travis-ci.org/flu-crew/smot)
![PyPI](https://img.shields.io/pypi/v/smot.svg)

# smot - Simple Manipulation Of Trees

`smot` is a command line tool for manipulating, summarizing, and sampling from
phylogenetic trees.


 | subcommand | description                                      |
 | ---------- | ------------------------------------------------ |
 | convert    | convert tree format                              |
 | tips       | list tip labels                                  |
 | plot       | plot the tree                                    |
 | sample     | sub-sample a tree                                |
 | factor     | integrate and/or infer classes for tips          |
 | tipsed     | regex-based search and replace across tip labels |
 | midpoint   | root tree by midpoint                            |
 | random     | make random tree given list of tip labels        |
 | clean      | remove singleton nodes and ladderize             |


## Installation

``` sh
pip install smot
```

## Requirements

Python modules:
 * biopython
 * parsec
 * docopt

Python v3.6 and later (required for string interpolation)

## Examples

Accessing usage information for each subcommand:

``` sh
smot -h
```


![](images/pdm-1.png)

``` sh
# image B
smot sample equal --factor-by-capture="(human|swine)" --keep="swine" --seed=42 --max-tips=2 pdm.tre > pdm-equal.tre
# image C
smot sample prop --proportion=0.1 --min-tips=2 --factor-by-capture="(human|swine)" --keep="swine" --seed=42 pdm.tre > pdm-prop.tre
# image D
smot sample para --proportion=0.1 --min-tips=2 --factor-by-capture="(human|swine)" --keep="swine" --seed=42 pdm.tre > pdm-para.tre
```

## Case study: Inferring human-to-swine influenza A virus transmission events
``` sh
# image B
smot sample equal --factor-by-capture="(human|swine)" --keep="swine" --seed=42 --max-tips=2 pdm.tre > pdm-equal.tre
# image C
smot sample prop --proportion=0.1 --min-tips=2 --factor-by-capture="(human|swine)" --keep="swine" --seed=42 pdm.tre > pdm-prop.tre
# image D
smot sample para --proportion=0.1 --min-tips=2 --factor-by-capture="(human|swine)" --keep="swine" --seed=42 pdm.tre > pdm-para.tre
```
Line 1 filters out all leaves with hosts other than swine or human. Line 2 removes all monophyletic swine clades that have no representative from 2021. Line 3 removes all swine clades represented by a single member. Line 4 removes any coloring in the input tree. Lines 5 colors all remaining swine clades orange (hexadecimal code “#FFA000”). Line 6 colors leaves gray by default, then colors swine orange and finally recent swine blue. Lines 8-9, 10-11, and 14-15 downsamples the human representatives using the equal, mono, and para algorithms, respectively. This script is based on smot v0.14.2, the API may change in the future.

