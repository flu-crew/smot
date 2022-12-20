---
title: '`smot`: a python package and CLI tool for contextual phylogenetic subsampling'
tags:
 - Python
 - phylogenetics
 - subsampling
 - influenza
authors:
  - name: Zebulun W. Arendsee
    orcid: 0000-0002-5833-798X
    affiliation: 1
  - name: Amy L. Vincent
    orcid: 0000-0002-4953-7285
    affiliation: 1
  - name: Tavis K. Anderson^[corresponding author]
    orcid: 0000-0002-3138-5535
    affiliation: 1
affiliations:
 - name: Virus and Prion Research Unit, National Animal Disease Center, USDA-ARS, Ames, IA, USA
   index: 1
date: 01 February 2022
bibliography: paper.bib
---

# Summary

`smot` (Simple Manipulation Of Trees) is a command line tool and Python package
with the pragmatic goal of distilling large-scale phylogenetic data to
facilitate visualization without jeopardizing inference. This package offers
subsampling algorithms that preserve reference taxa and tree topology,
algorithms for classifying unlabeled tips given a subset of labeled reference
tips, and functions for filtering phylogenetic trees. The `smot` tool has broad
application in phylogenetic analysis and we demonstrate its utility using a
genomic epidemiology study of influenza A virus in swine.

# Statement of Need

Molecular phylogenetic analysis is initiated through the generation of a
sequence dataset, followed by multiple sequence alignment, phylogenetic tree
inference, and the identification of evolutionary relationships of interests
[@baldauf2003phylogeny]. Given the rapid generation of large molecular sequence
datasets, phylogenetic trees can become cumbersome and it may be necessary to
subset data to address specific hypotheses or to facilitate visualization. For
example, in a phylogenetic tree with thousands of taxa that are clustered into
many monophyletic groups, the user may want to subsample the taxa while
ensuring all groups and their evolutionary relationships are represented in the
visualized tree. Alternatively, taxa on trees may be described and grouped by
variables not defined by common ancestry such as geographical regions,
phenotypes, sequence motifs, or host species and this information may be
incomplete and require classification. In these cases, subsampling and
classifying data on the phylogenetic tree can form the basis of hypotheses on
how temporal, spatial, and other processes correlate with the evolutionary
history of the studied population [@baum2005tree; @baum2013tree]. Developing
appropriate hypotheses can be facilitated through the subsampling, classifying,
and filtering algorithms in `smot`.

The utility of `smot` is explained by the following three cases. For
subsampling, `smot` may process a phylogenetic tree that has labeled clades:
taxa from each clade may be subsampled while maintaining a set number of taxa
from each clade and also retaining provided reference taxa. Alternatively, the
number of taxa within a clade may be scaled as $n_{sampled}=n^{1/r}$, where
$n$ is the original number of taxa in the clade and $r$ is a user provided scaling
factor.  For classification, `smot` can process a partially labeled tree by
inferring missing labels and prepending them to the taxa names. For filtering,
`smot` takes a tree with user-provided trait labels and then removes, subsamples
or edits any monophyletic subtrees that meet specific criteria. The subsequent
section will briefly introduce related tools currently applied in phylogenetic
analyses and outline the role `smot` can play in a phylogeneticist’s toolbox.



# Related Work

The first purpose of `smot` is subsampling. Phylogenetic subsampling has been
extensively researched [@mongiardino2021phylogenomic]. It may be used to remove
sequences with quality problems or to reduce the dataset prior to
computationally expensive operations. Programs such as Treemmer
[@menardo2018treemmer], TreeTrimmer [@maruyama2013treetrimmer], and Treeshrink
[@mai2018treeshrink] approach the general problem of statistical subsampling
while preserving specific diversity metrics of the original inferred
phylogenetic tree. In contrast, `smot` is designed to subsample from groups
within trees while preserving desired references.

The second purpose of `smot` is classification where unlabeled taxa in a tree
are classified using a subset of labeled taxa. This is achieved by either
patristic distance or monophyletic grouping. The method is based on
submitted reference taxa rather than inferring clusters from the tree and then
naming them. Inferring clusters de novo can be accomplished with tools such as
phyCLIP [@han2019phyclip] or DYNAMITE [@magalis2021dynamite].  Alternatively,
taxa may be classified into clades using a fixed reference scaffold tree; this
is done for influenza A virus in swine by `octoFLU` [@chang2019octoflu]. `smot`
depends on reference taxa, like `octoFLU`, but it extracts them from the taxa
names or tables of attributes.

The third purpose of `smot` is filtering and coloring a tree based upon user
queries. `smot` does not have more specialized phylogenetic and visualization
utilities; these are be provided by phylommand [@ryberg2016phylommand] and ETE
suite-toolkit [@huerta-cepas2016ete] in Python and ggtree in R [@yu2017ggtree].
However, `smot` may be easily integrated into analytical pipelines as a module
and can be used to set leaf and branch coloring, which may then be visualized
with a tree viewer such as FigTree.

`smot` is primarily designed to be used as a command line tool, but it can also
be imported as a Python package. It complements the existing Python
phylogenetics ecosystem through its subsampling, classifying, and filtering
algorithms. Currently, Python packages for phylogenetics include the Phylo
module of Biopython [@cock2009biopython], the ETE-toolkit
[@huerta-cepas2016ete], DendroPy [@sukumaran2010dendropy], and TreeSwift, which
offers a scalable foundation for building algorithms that work on large trees
[@moshiri2020treeswift].



# Core Algorithms

A common theme across `smot`'s algorithms is to group tips and then perform an
action on each group. All grouping algorithms require labels on some or all of
the tips. Labels may be assigned to tips using entries provided in a table,
input field index given a text separator in taxa names, or through application
of regular expressions captures over taxa names. Given these initial labels,
the tree can be grouped using a patristic, monophyletic, or paraphyletic
algorithm. The patristic algorithm groups all tips together under the label of
the nearest labeled tip by branch distance on the tree. The monophyletic
algorithm descends from root to tip (trees are assumed to be rooted). When a
subtree with one or more tips share a common label, and all other tips are
unlabeled, the subtree is yielded as one monophyletic group. The paraphyletic
algorithm also descends from root to tip, but rather than setting a
monophyletic subtree to a group, it merges adjacent monophyletic groups with
the same label down the tree. When a node is reached that is monophyletic for
the two subtrees with different labels, each subtree is set as a group,
ensuring that the branch nearest to a group border is sampled from. See **Figure
1** for an simple example of the difference between the monophyletic and
paraphyletic grouping algorithms.

![The monophyletic and paraphyletic algorithms differ in how they group the clades that will be downsampled (or otherwise acted upon). The paraphyletic algorithm groups adjacent monophyletic subtrees down the trunk but preserves the deepest monophyletic tree to guarantee that the nearest relative to a change in label is preserved.\label{fig:fig1}](img/fig1.png)

Once a tree is partitioned into groups, it may be subsampled, classified, or
filtered. Subsampling takes each partition and randomly selects either a set
proportion of the tips (with an optional minimum tips) or a proportion that
scales with group size. For scaled sampling, the number of sampled taxa equals
$n^{1/r}$, where $n$ is the number of tips in the group and $r$ is the root
(e.g., 2 for square root). Classifying either propagates the group label to all
unlabeled members or assigns each unlabeled tip the label of the nearest
labeled tip using a patristic classifier. Filtering performs an operation on
each group under some condition, for example, it may delete all groups that
have fewer than $n$ members.

![Interspecies transmission and evolution of the 2009 H1N1 influenza A virus pandemic (H1N1pdm09) lineage in swine and humans. (A) An inferred phylogenetic tree of influenza A virus (IAV) in swine hemagglutinin (HA) genes from the H1N1pdm09 lineage collected between 2015 and 2021. There are too many swine strains in the tree to read the labels even omitting the human influenza A virus H1N1 HA sequences necessary to capture the correct evolutionary context of the lineage. (B) An inferred phylogenetic tree of H1N1pdm09 lineage HA genes from humans and swine (26,802 genes, human in black, swine in orange). The tree is too large to see individual labels, and critical human-to-swine evolutionary linkage is obscured. To identify the evolutionary history of this IAV lineage, we include all swine HA genes to demonstrate onward transmission of the virus, and human HA genes to detect directionality of interspecies transmission. (C) An application of `smot`: human HA genes were down-sampled while keeping all swine genes. This ensured the context of human HA genes, allowing identification of human-to-swine spillovers and visualization of swine-to-swine transmission of the H1N1pdm09 lineage. All swine clades present in (B) are present in (C). (D) Using this approach, we identified a human-to-swine event (arrow) that seeded onward transmission in swine, followed by a single human HA gene nested within a monophyletic swine group (triangle) (blue rectangle in (C) and enlarged in the inset (D)). The human HA gene demonstrates a zoonotic (swine-to-human) transmission event. Subsampling human HA genes before building the tree or without considering context would likely obscure these two-way interspecies transmission events.\label{fig:f2}](img/fig2.png)

# Case Study: Inferring human-to-swine influenza A virus transmission events

In 2009, an influenza A virus emerged in swine and was transmitted to humans
causing the first pandemic of the 21st century [@smith2009origins]. This H1N1
lineage (H1N1pdm09) became endemic in humans and is regularly reintroduced to
swine populations globally [@vijaykrishna2010reassortment;
@nelson2015continual].  Phylogenetically, human-to-swine introductions can be
detected based upon tree topology: an isolated swine-derived hemagglutinin (HA)
gene nested within a monophyletic group of human genes indicates interspecies
transmission [@volz2013viral]. A similar tree structure can be used to infer
zoonotic transmission from swine to humans [@nelson2015continual]. To
illustrate the shared evolutionary history of the H1N1pdm09 lineage, we
inferred phylogenetic trees based on the HA genes collected from only swine
(**Figure 2A**) and from swine and human sequences together (**Figure 2B**). In
both cases, the size of the tree required to infer host origin and interspecies
transmission events obscured visualization and the ability to infer the
directionality of the transmission events.

The goal of this case study was to identify subsequent swine-to-swine
transmission of H1N1pdm09 that descended from unique human-to-swine spillovers.
To achieve this, we downloaded all swine and human H1N1pdm09 hemagglutinin (HA)
genes sequences from the Influenza Research Database [@zhang2017influenza]. Each gene
sequence was labeled through the database search interface by virus strain
name, host (human or swine), collection location, and date of collection. The
HA genes were aligned with MAFFT [@katoh2013mafft], and a maximum likelihood tree
was inferred using a general time reversible model of molecular evolution with
gamma distributed rate variation in FastTree [@price2010fasttree]. To phylogenetically
identify contemporary and sustained transmission of H1N1pdm09 in swine, we:
subsampled large human clades; removed swine taxa with no recently observed
representatives; and removed swine clades that had no evidence of
swine-to-swine transmission (i.e., clades with a single representative).

![Cleaning and subsampling process to extract a phylogenetic tree for visualization and inference. The `smot`-processed phylogenetic tree can be used to identify human-to-swine spillover and sustained transmission of the 2009 H1N1 influenza A virus pandemic (H1N1pdm09) lineage in swine. (A) The original phylogenetic tree with human and swine H1N1pdm09 HA genes (n=26802) collected between 2009 and 2021. (B) The tree after filtering to keep only the swine clades that had more than one member and at least one 2021 representative. (C-E) The trees after subsampling with the (C) equal, (D) mono, and (E) para algorithms, respectively. Tip labels colored in orange represent swine hosts and orange branch coloring represents clades where all hosts are swine; blue tip labels are swine HA genes collected in 2021; each swine subtree represents an independent H1N1pdm09 clade circulating in US swine derived from a unique human-to-swine spillover event.  The `smot` pipeline that produced the trees (C-E) was written in Bash and documentation and explanation of the code is provided in the GitHub README (<https://github.com/flu-crew/smot>) or the Flu Crew documentation page (<https://flu-crew.github.io/docs/>).\label{fig:f3}](img/fig3.png)

This process was achieved with a series of `smot` commands (**Figure 3**).
First, `smot` extracted clades where all taxa labels where annotated with
either the term "human" or "swine". We then removed all monophyletic swine
clades without a detection in 2021 and all swine clades with a single member
(i.e., isolated spillovers without evidence of sustained transmission). The
resultant tree contained all human HA genes and swine HA genes for strains with
evidence of contemporary circulation (**Figure 3B**): this tree was then
subsampled with the three `smot` algorithms (**Figure 3C-E**). In **Figure
3C**, we sampled 1 tip from each monophyletic human clade and generated a tree
that demonstrated unique human and swine monophyletic clades. A similar
presentation was generated in **Figure 3D** where the algorithm randomly
selected $n^{1/4}$ tips from each monophyletic human clade, where $n$ is the
number of tips in the original clade, keeping a minimum of 1 tip. The third
algorithm (**Figure 3E**) sampled paraphyletically, allowing human branches
across the backbone to be jointly subsampled, allowing greater compression of
the tree and more tractable visualization. The final tree (**Figure 3E**)
demonstrated seven independent H1N1pdm09 human-to-swine spillover events with
evidence of persistent swine-to-swine transmission Importantly, the tree was
sufficiently compressed for labels to be readable on a single page while still
providing the human context HA genes needed to resolve the seven unique
human-to-swine spillover events.

\scriptsize
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
\normalsize

# Availability

`smot` is available on PyPi and the source is hosted on GitHub at <https://github.com/flu-crew/smot>. Additional documentation is available in the Flu Crew documentation page (<https://flu-crew.github.io/docs/>).

# Acknowledgements

We gratefully acknowledge pork producers, swine veterinarians, and laboratories for participating in the USDA Influenza A Virus in Swine Surveillance System and publicly sharing sequences. This work was supported in part by: the U.S. Department of Agriculture (USDA) Agricultural Research Service (ARS project number 5030-32000-231-000-D); the U.S. Department of Agriculture (USDA) Animal and Plant Health Inspection Service (ARS project number 5030-32000-231-080-I); the National Institute of Allergy and Infectious Diseases, National Institutes of Health, Department of Health and Human Services (contract number 75N93021C00015); the USDA Agricultural Research Service Research Participation Program of the Oak Ridge Institute for Science and Education (ORISE) through an interagency agreement between the U.S. Department of Energy (DOE) and the USDA Agricultural Research Service (contract number DE-AC05- 06OR23100); and the SCINet project of the USDA Agricultural Research Service (ARS project number 0500-00093-001-00-D). The funders had no role in study design, data collection and interpretation, or the decision to submit the work for publication. Mention of trade names or commercial products in this article is solely for the purpose of providing specific information and does not imply recommendation or endorsement by the USDA, DOE, or ORISE. USDA is an equal opportunity provider and employer.

# References
