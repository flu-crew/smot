0.5.0 [2020-08-09]

 * remove midpoint command - it was too slow to be useful, there are better CLI
   tools for this job
 * Fix bug preventing STDIN

0.4.0 [2020-08-06]

 * update CLI interface
   - subcommand documentation
   - documentation for each field
   - cleaner argument checking

0.3.0 [2019-12-04]

 * allow automatic reading of NEXUS
 * remove '--format' option (infer input format and write newick)
 * add BioPython-based convert function
 * let factors be appended or prepended to tip labels
 * merge sampling commands
 * ladderize tree before plotting
 * `clean` command also ladderizes the tree 

0.2.0 [2019-11-20]

 * add factor imputing
 * add `--seed` argument to `smot random`
 * mix bug in proportional sampler
 * add tests of the command line utility
 * fix bug in unfactored proportional sample
 * allow the default factor

0.1.0 [2019-11-19]

 * initial release
