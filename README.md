![build status](https://github.com/flu-crew/smot/actions/workflows/python-app.yml/badge.svg)
![PyPI](https://img.shields.io/pypi/v/smot.svg)

# smot - Simple Manipulation Of Trees

`smot` is a command line tool for sampling and manipulating phylogenetic trees.


## Installation

`smot` is available through PyPi and dependes on Python 3.7. In can be installed as follows:


``` sh
pip install smot
```

It may be necessary to replace `pip` with `pip3`.

## Documentation

You can access usage information from the command line:

```
$ smot -h
Usage: smot [OPTIONS] COMMAND [ARGS]...

  Simple Manipulation Of Trees

Options:
  -v, --version  Show the version and exit.
  -h, --help     Show this message and exit.

Commands:
  color   Color the leafs or branches.
  factor  Impute, annotate with, and/or tabulate factors.
  filter  An advanced tool for performing actions (remove, color, sample,...
  grep    Prune a tree to preserve only the tips with that match a pattern.
  sample  Subsample the tree using various methods.
  tips    Print the tree tip labels.
  tipsed  Search and replace patterns in tip labels.

  For subcommand usage, append `-h` (e.g., smot color -h)
```

Detailed information can then be requested for the specific subcommand:

```
$ smot grep -h
Usage: smot grep [OPTIONS] PATTERN [TREE]

  Prune a tree to preserve only the tips with that match a pattern.

Options:
  -v, --invert-match  Keep all leaves NOT matching the pattern
  -P, --perl          Interpret the pattern as a regular expression
  -f, --file          Read patterns from a file instead of a set string
  --newick            Write output in simple newick format (tip colors and
                      metadata will be lost)

  -h, --help          Show this message and exit.
```

Some subcommands have further subcommands and specific usage information can be
found for each. For example:

```
$ smot sample -h
$ smot sample para -h 
```

## Tree formats

Input is Newick or Nexus format and output is Nexus unless a `--newick` flag is
set. Choosing Newick output will lose any color metadata.

## Examples

### Example 1

Starting from the influenza A virus in pandemic tree, three subsamples can be
drawn and colored as follows:

```sh
smot grep -v "(swine|human)" pdm.tre |
    smot filter --factor-by-capture="(swine|human)" --all-match="swine" --none-match="2021-" --remove |
    smot filter --factor-by-capture="(swine|human)" --all-match="swine" --smaller-than 2 --remove |
    smot color rm |
    smot filter --factor-by-capture="(swine|human)" --all-match="swine" --color="#FFA000" |
    smot color leaf -P -p "." "#909090" -p "swine" "#FFA000" -p "swine.*2021-" "#0000FF" > select-swine.tre

smot sample equal select-swine.tre --factor-by-capture="(swine|human)" \
  --max-tips=1 --keep="swine" > select-swine-equal-sample.tre

smot sample mono select-swine.tre --scale=4 --factor-by-capture="(swine|human)" \
  --min-tips=1 --keep="swine" --seed=42 > select-swine-mono-sample.tre

smot sample para select-swine.tre --scale=4 --factor-by-capture="(swine|human)" \
  --min-tips=3 --keep="swine" --seed=42 > select-swine-para-sample.tre
```

Line 1 filters out all leaves with hosts other than swine or human. Line 2
removes all monophyletic swine clades that have no representative from 2021.
Line 3 removes all swine clades represented by a single member. Line 4 removes
any coloring in the input tree. Lines 5 colors all remaining swine clades
orange (hexadecimal code “#FFA000”). Line 6 colors leaves gray by default, then
colors swine orange and finally recent swine blue. Lines 8-9, 10-11, and 14-15
downsamples the human representatives using the equal, mono, and para
algorithms, respectively. This script is based on smot v0.14.2, the API may
change in the future.

![](images/pdm-0.png)

In the above figure, (A) is the unsampled tree with all human (black) and swine
(orange) pandemic strains, (B) removes all monophyletic swine branches that
have only a single representative, and (C-E) subsample tree B using the
*equal*, *mono* and *para* algorithms.

### Example 2

![](images/pdm-1.png)

``` sh
# image B
smot sample equal --factor-by-capture="(human|swine)" --keep="swine" --seed=42 --max-tips=2 pdm.tre > pdm-equal.tre
# image C
smot sample prop --proportion=0.1 --min-tips=2 --factor-by-capture="(human|swine)" --keep="swine" --seed=42 pdm.tre > pdm-prop.tre
# image D
smot sample para --proportion=0.1 --min-tips=2 --factor-by-capture="(human|swine)" --keep="swine" --seed=42 pdm.tre > pdm-para.tre
```

## Examples by subcommand

This section will show examples for each subcommands. All of the examples can
be executed using sample files available in the `test-data` folder in this
repo.

### `smot grep` - prune a tree to preserve only the taxa matching a pattern

Create a subtree where all taxa are from the year 2020.The `-..-..` pattern is
a regular expression that matches the MONTH-DAY syntax in a date.

```
smot grep --perl '2020-..-..' 1B.tre
```

### `smot factor` - Impute, annotate with, and/or tabulate factors

Associating "factors" with taxa is used across `smot` for annotating, sampling
and coloring. These factors can be specified in one of several ways.

 * `--factor-by-capture` uses a regular expression capture group to set the factor
 * `--factor-by-field` uses the index of a delimited field in the taxon label
 * `--factor-by-table` uses a two-column, TAB-delimited table that maps taxon name to factor

The `smot factor` subcommand can list the extracted factors in a table:

```
$ smot factor table --factor-by-capture "(1B[^|]*)" 1B.tre | head
publicIAV|A/swine/Minnesota/A02245706/2020|H1N2|swine|USA|1B.2.1|2020-07-30     1B.2.1
publicIAV|A/swine/Minnesota/A02245749/2020|H1N2|swine|USA|1B.2.1|2020-10-15     1B.2.1
publicIAV|A/swine/Minnesota/A02245719/2020|H1N2|swine|USA|1B.2.1|2020-09-28     1B.2.1
publicIAV|A/swine/Minnesota/A02524813/2020|H1N2|swine|USA|1B.2.1|2020-10-27     1B.2.1
```

Or it can return the input tree with the factors appended or prepended to the
taxon name (`smot factor append` and `smot factor prepend`, respectively).

### `smot sample` - subsample the tree

`smot` offers three general sampling algorithms.

 * The `equal` sampling method recursively samples an equal number of taxa from
   each subtree descending from each node. If a subtree does contains too few
   taxa, the remainder will be distributed to the sister subtrees.

 * The monophyletic sampling method (`mono`) subsamples a branch of the tree if
   all taxa within the branch have the same factor.

 * The paraphyletic sampling method (`para`) allows adjacent branches that are
   monophyletic to be sampled together. The algorithm guarantees that at least
   one taxa is sampled from the deepest branch neighboring a different group.

The following three commands use the `mono` algorithm to sample 25% of the taxa
from each of the 1B flu clades. They differ only in how the factor (the strain
clade) is specified:

```
smot sample mono --seed=24601 --factor-by-field=6 -p 0.25 1B.tre
smot sample mono --seed=24601 --factor-by-table 1B.tab -p 0.25 1B.tre
smot sample mono --seed=24601 --factor-by-capture "\|(1B\.[^|]*)" -p 0.25 1B.tre
```

The `--seed` allows the random seed to be set for reproducibility.

It may be useful to prevent certain taxa from being downsampled. For example
reference taxa or taxa that are from a particular time or region of interest.
This can be achieved with the `-k/--keep` and `--r/--keep-regex` options which
prevents downsampling of specific factors or taxa with labels matching a given
regular expression. In the example below, a tree is downsampled by clade
(`1B.*`) but all taxa from the 2020s and all taxa from the specific clade
"1B.1.2" are preserved:

```
smot sample mono --factor-by-capture="(1B\.[^|]*)" -p 0.1 -r "202.-..-" -k "1B.1.2" --min-tips=3 1B.tre
```

Rather than taking a set percentage of representatives in each sampling group,
the sample percentage can vary with the size of the group. Given a group of
size `n`, we can downsample the group to a size of `ceiling(n^(1/r))`, where
`r` is the root specified by the `-s/--scale` option. This is useful when
over-represented clades obscure the features of interest.

```
smot sample mono --factor-by-capture="(1B\.[^|]*)" -s 3 --min-tips=3 1B.tre
```

The final sampling method is to randomly sample a set number of taxa from each group (`-n/--number`):

```
smot sample mono --factor-by-capture="(1B\.[^|]*)" -n 3 --min-tips=3 1B.tre
```

The `para` algorithm is useful for sampling features that may not be inherited
by the child. Examples include variable phenotypes, geographical location, or
pathogen host. The examples below sample flu strains from a tree with frequent
interspecies jumps.

```
smot sample para --factor-by-capture="(swine|human)" -p 0.1 --min-tips=5 pdm.tre
smot sample para --factor-by-capture="(swine|human)" -s 2 --min-tips=5 pdm.tre
smot sample para --factor-by-capture="(swine|human)" -n 3 pdm.tre
```

### `smot color` - color taxa labels or branches

Taxa labels may be colored by specifying a pattern and the color matching
labels will be given. For example, coloring every taxa orange ("#FFA500" in
hex) that has the word "swine" and every label that was from year 2020 green
can be done as follows: 

smot color leaf -p swine "#FFA500" -p "2020-" "#00FF00" 1B.tre

Note that multiple patterns may be specified in one command and that latter
matches overwrite the color of prior matches.

Insted of matching fixed patterns, regular expressions may be matched instead
using the `--perl` argument:

smot color leaf --perl -p "202[012]-..-..$" "#00FF00" 1B.tre

For coloring branches, the same `--factor-by-*` options as were seen in the
`smot sample` examples may be used. `smot` will automatically generate colors
for each factor:

```
smot color branch mono --factor-by-capture="(1B\.[^|]*)" 1B.tre
```

If you want to explicitly set the colors of each factor, you can provide a
TAB-delimited table mapping factors to colors:

```
smot color branch mono --factor-by-capture="(1B\.[^|]*)" --colormap=1B-colors.tab 1B.tre
```

Again, the `para` sampling algorithm may be used for traits that are spread across the tree:

```
smot color branch para --factor-by-capture="(swine|human)" pdm.tre
smot color branch para --factor-by-capture="(swine|human)" --colormap=pdm-colors.tab pdm.tre
```

If you want to color taxa labels by branch, or color lower branches the same
color as the parent branch, you can pass the tree into `smot color push`:

```
smot color branch mono --factor-by-field 1 -c 1B-colors.tab 1B.tre | smot color push
```

### `smot filter` - subset or modify taxa by group

The `smot filter` family of function allows special operations to be performed
on the groups within a tree. Currently only the `mono` algorithm is supported
for finding these groups.

Color all monophyletic swine branches red if they contain at least one taxa from 2021: 

```
smot filter --factor-by-capture="(swine|human)" --all-match="swine" --some-match="2021" --color="#FF0000" pdm.tre
```

Remove any monophyletic group that contain only a single taxa:

```
smot filter --factor-by-capture="(swine|human)" --smaller-than=2 --remove pdm.tre
```

Subsample any monophyletic group that is larger than 10:

```
smot filter --factor-by-capture="(1B[^|]*)" --larger-than=10 --sample=0.1 1B.tre
```
