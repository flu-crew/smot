0.15.0 [2021-08-08]
===================

 * Add `stat` subcommand 
 * Replace `sample prop` with `sample mono`. This contrasts with `para`.
 * Add -v/--version option

0.14.2 [2021-09-14]
===================

 * Fix several issues found my flake8
 * Fix --factor-by-table option and documentation
 * Keep tip colors after tipsed

0.14.1 [2021-07-19]
===================

 * More robust color map parsing

0.14.0 [2021-06-07]
===================

 * Add `-n NUM` option to samplers to select NUM elements from each group
 * Fix bug in sampling from root - the two sides under root were always
 sampled independently. With -n option, this led to twice too many selections
 when no factoring was done. With proportional options, the bug would only
 cause problems in the corner case where one side under root had fewer than
 minTips tips.

0.13.1 [2021-05-19]
===================

 * Add `filter` subcommand

0.12.1 [2021-05-06]
===================

 * Fix KeyError raised when a factor is not in the color table, resolve by
   simply not coloring the element

 * Fix tree formatting when using color maps (trim whitespace)

0.12.0 [2021-04-23]
===================

 * Add `color rm` to remove all coloring annotations, with the `--newick`
   option, this also clears all metadata (e.g., FigTree annotations)

 * Fixed bugs in regex captures and para coloring

0.11.0 [2021-04-21]
===================

 * Add monophyletic and paraphyletic branch coloring

 [FYI - due to ghosts in pyp, v0.10.0 is gone]

0.9.0 [2021-04-20]
==================

 * Add `color` command

   `smot color -p "swine" "#FFA500" -p "2020-" "#00FF00" my.tre > color.tre`

 * Print to nexus by default, preserving figtree colors and settings, with
   `--newick` option for printing raw newick trees.

 * Remove `plot`, `convert`, and `random` commands and the the `biopython`
   dependency. These commands were not well-supported and their dependency was
   very heavy. Use phylomander or dedicated plotting packages instead.

 * Remove `clean` function - I may bring this back in the future, but at the
   moment there isn't an obvious use-case for `clean`.

 * Add support for parsing metadata from and writing Nexus - the main need for
   this is to properly handle tip colors and preserve metadata.

0.8.2 [2021-04-13]
==================

 * Add test for unicode support (e.g., Chinese characters or emoticons)

 * Add parser support for escaping characters. Any character following a '\' is
   kept, so quotes within strings and backslashes can be escaped. Special
   characters are not supported (e.g., substituting '\t' for a TAB character).

 * Add parser support for FigTree's weird single-quote escape convention. They
   replace within-string single-quotes with a pair of single-quotes.

0.8.1 [2021-04-09]

 * add `--keep-regex` option for `sample prop`

0.8.0 [2021-04-08]

 * add `--keep-regex` option

0.7.1 [2021-03-26]
------------------

 * remove debugging crap

0.7.0 [2021-03-26]
------------------

 * allow factor imputation through patristic distance 

0.6.0 [2021-03-26]
------------------

 * add power scaling option to samplers
 * add grep

0.5.0 [2020-08-09]
------------------

 * remove midpoint command - it was too slow to be useful, there are better CLI
   tools for this job
 * Fix bug preventing STDIN

0.4.0 [2020-08-06]
------------------

 * update CLI interface
   - subcommand documentation
   - documentation for each field
   - cleaner argument checking

0.3.0 [2019-12-04]
------------------

 * allow automatic reading of NEXUS
 * remove '--format' option (infer input format and write newick)
 * add BioPython-based convert function
 * let factors be appended or prepended to tip labels
 * merge sampling commands
 * ladderize tree before plotting
 * `clean` command also ladderizes the tree 

0.2.0 [2019-11-20]
------------------

 * add factor imputing
 * add `--seed` argument to `smot random`
 * mix bug in proportional sampler
 * add tests of the command line utility
 * fix bug in unfactored proportional sample
 * allow the default factor

0.1.0 [2019-11-19]
------------------

 * initial release
