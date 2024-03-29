# This makefile will test the expected against observed output.
# If the make command fails, then there is a problem

all:
	smot sample para --newick --proportion=0.3 --min-tips=2 --factor-by-field=2 --seed=42 --keep=S fork.tre > .obs-fork.tre
	diff .obs-fork.tre .exp-fork.tre
	smot tips fishbone.tre > .obs-tips.txt
	diff .exp-tips.txt .obs-tips.txt
	smot tipsed --newick X Y fishbone.tre > .obs-tipsed.txt
	diff .exp-tipsed.txt .obs-tipsed.txt
	smot sample equal --newick --factor-by-field=2 --keep="S" --max-tips=2 --zero polytomyHS.tre > .obs-polytomyHS-equal.txt
	diff .exp-polytomyHS-equal.txt .obs-polytomyHS-equal.txt
	smot sample mono --newick --seed=42 --factor-by-field=2 --proportion=0.2 --keep="S" --min-tips=2 polytomyHS.tre > .obs-polytomyHS-prop.txt
	diff .exp-polytomyHS-prop.txt .obs-polytomyHS-prop.txt
	smot sample para --newick --seed=42 --factor-by-field=2 --proportion=0.2 --keep="S" --min-tips=2 polytomyHS.tre > .obs-polytomyHS-para.txt
	diff .exp-polytomyHS-para.txt .obs-polytomyHS-para.txt
	# this should randomly sample 15 taxa of th 1591 that are in H1.tre
	smot sample mono --proportion=0.01 --min-tips=3 --seed=42 H1.tre | smot tips | wc -l | sed 's/ //g' > a
	echo 15 > b
	diff a b
	# this should proportionally sample while retaining all global clades and unknowns representatives
	smot sample mono --newick --proportion=0.01 --min-tips=3 --seed=42 --factor-by-capture='(Other-Human[^|]*|1[ABC]\.[.0-9]*)' H1.tre > .obs-h1-factored-prop.tre
	diff .obs-h1-factored-prop.tre .exp-h1-factored-prop.tre
	# set default factor to NA, then list
	smot factor table --default=NA fishbone.tre > .obs-factor-default.txt
	diff .exp-factor-default.txt .obs-factor-default.txt
	smot factor prepend --newick --default=NA fishbone.tre > .obs-factor-prepend-default.txt
	diff .exp-factor-prepend-default.txt .obs-factor-prepend-default.txt
	smot factor append --newick --default=NA fishbone.tre > .obs-factor-append-default.txt
	diff .exp-factor-append-default.txt .obs-factor-append-default.txt
	rm .obs-*
	# test patristic factorizer
	smot factor table --patristic --factor-by-capture="(H|S)" partial-fishbone-1.tre > .obs-para-impute-1
	diff .obs-para-impute-1 .exp-para-impute-1
	#
	smot factor table --patristic --factor-by-capture="(H|S)" partial-fishbone-2.tre > .obs-para-impute-2
	diff .obs-para-impute-2 .exp-para-impute-2
	# test parsing of newich and nexus files
	smot tips H1.tre > a
	smot tips H1.nexus > b
	diff a b
	# test grep on 1B.tre
	smot grep "|1B.1.2|" 1B.tre | smot tips > a
	smot tips 1B.tre | grep "|1B.1.2|" > b
	diff a b
	# test reverse grep
	smot grep -v "|1B.1.2|" 1B.tre | smot tips > a
	smot tips 1B.tre | grep -v "|1B.1.2|" > b
	diff a b
	# test regex grep
	smot grep -P "(1B.1.2\\||1B.1.2.1)" 1B.tre | smot tips > a
	smot tips 1B.tre | grep -E "(1B.1.2\\||1B.1.2.1)" > b
	diff a b
	# test file grep
	smot grep -f patterns 1B.tre | smot tips > a
	smot tips 1B.tre | grep -f patterns > b
	diff a b
	# clean up
	# para with keep-regex
	smot sample para --newick --min-tips=3 -p 0.1 --seed 42 --keep-regex="(CVV|variant|accine|eference|Consensus)" --factor-by-capture="(1B[^|]*|Other-Human[^|]*)" 1B.tre > a
	diff a .1B-para-keep.tre
	# prop with keep-regex
	smot sample mono --newick --min-tips=3 -p 0.1 --seed 42 --keep-regex="England" --factor-by-capture="(swine|human)" pdm.tre > a.tre
	diff a.tre .pdm-prop-keep.tre
	smot grep England a.tre | smot tips | wc -l > a
	smot tips pdm.tre | grep England | wc -l > b
	diff a b
	# ensure nexus data is created properly, preserving colors
	smot grep Minnesota problem-with-grep.tre > a.tre
	diff a.tre .exp-grep.tre
	# check coloring
	smot color leaf -p "X." "#990000" -p "X1" "#009900" -P fork.tre > a.tre
	diff a.tre .exp-color-fork.tre
	# color branches
	smot color branch mono --factor-by-capture="(1B\.[^|]*)" 1B.tre > a.tre
	diff .exp-1B-color.tre a.tre
	# color branches with colormap
	smot color branch mono --factor-by-capture="(1B\.[^|]*)" --colormap all-colors.txt 1B.tre > a.tre
	diff .exp-1B-mapcolor.tre a.tre
	# color branches with para
	smot color branch para --factor-by-capture="(1B.[^|]*)" 1B.tre > a.tre
	diff .exp-1B-mapcolor-para.tre a.tre
	# color removal
	smot color branch mono --factor-by-capture="(1B\.[^|]*)" --colormap all-colors.txt 1B.tre | smot color leaf -p CVV "#FF0000" | smot color rm --newick > a.tre
	diff 1B.tre a.tre
	# check filter
	smot filter --factor-by-capture="(swine|human)" --none-match=Ohio --all-match=swine --remove pdm.tre > a.tre
	diff a.tre .exp-ohio-pdm
	smot grep human pdm.tre | smot tips | sort > a
	smot grep human a.tre | smot tips | sort > b
	diff a b
	# check factor-by-table
	smot factor table --factor-by-table=fishbone-table.txt unfactored-fishbone.tre --impute > a
	diff a fishbone-table-factored.txt
	# check color push and pull
	smot color pull 1B-partial-color.tre > z.tre
	diff z.tre 1B-full-color.tre
	smot color push 1B-spotty-color.tre > z.tre
	diff z.tre 1B-full-color.tre
	# polytomies are correctly handled by sample para
	# * three random tests for presence of root
	smot sample para -p 0.1 --factor-by-capture="([HS])" polytomyHS-v2.tre | smot tips | grep -E '(X1|X2|X3)\|' 
	smot sample para -p 0.1 --factor-by-capture="([HS])" polytomyHS-v2.tre | smot tips | grep -E '(X1|X2|X3)\|' 
	smot sample para -p 0.1 --factor-by-capture="([HS])" polytomyHS-v2.tre | smot tips | grep -E '(X1|X2|X3)\|' 
	# all swine are present
	smot sample para -p 0.1 --factor-by-capture="([HS])" polytomyHS-v2.tre | smot tips | grep S | sort > a
	smot tips polytomyHS-v2.tre | grep S | sort > b
	diff a b
	# zero min-tips test
	smot sample mono --min-tips=0 -p 0.1 --factor-by-capture "(swine|human)" --seed=42 pdm.tre > a
	diff a .pdm_zero-min-tips.tre
	# cleanup
	rm -f a b a.tre b.tre
