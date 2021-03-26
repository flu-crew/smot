# This makefile will test the expected against observed output.
# If the make command fails, then there is a problem

all:
	smot sample para --proportion=0.3 --min-tips=2 --factor-by-field=2 --seed=42 --keep=S fork.tre > .obs-fork.tre
	diff .obs-fork.tre .exp-fork.tre
	smot tips fishbone.tre > .obs-tips.txt
	diff .exp-tips.txt .obs-tips.txt
	smot tipsed X Y fishbone.tre > .obs-tipsed.txt
	diff .exp-tipsed.txt .obs-tipsed.txt
	smot tips fishbone.tre | smot random --seed=42 > .obs-random.txt
	diff .exp-random.txt .obs-random.txt
	smot sample equal --factor-by-field=2 --keep="S" --max-tips=2 --zero polytomyHS.tre > .obs-polytomyHS-equal.txt
	diff .exp-polytomyHS-equal.txt .obs-polytomyHS-equal.txt
	smot sample prop --seed=42 --factor-by-field=2 --proportion=0.2 --keep="S" --min-tips=2 polytomyHS.tre > .obs-polytomyHS-prop.txt
	diff .exp-polytomyHS-prop.txt .obs-polytomyHS-prop.txt
	smot sample para --seed=42 --factor-by-field=2 --proportion=0.2 --keep="S" --min-tips=2 polytomyHS.tre > .obs-polytomyHS-para.txt
	diff .exp-polytomyHS-para.txt .obs-polytomyHS-para.txt
	# this should randomly sample 15 taxa of th 1591 that are in H1.tre
	smot sample prop --proportion=0.01 --min-tips=3 --seed=42 H1.tre | smot tips > .obs-h1-hundreth-sample-prop.txt
	diff .obs-h1-hundreth-sample-prop.txt .exp-h1-hundreth-sample-prop.txt
	# this should proportionally sample while retaining all global clades and unknowns representatives
	smot sample prop --proportion=0.01 --min-tips=3 --factor-by-capture='(1[ABC]\.[0-9.]*)' --seed=42 H1.tre > .obs-h1-factored-prop.tre
	diff .obs-h1-factored-prop.tre .exp-h1-factored-prop.tre
	# set default factor to NA, then list
	smot factor table --default=NA fishbone.tre > .obs-factor-default.txt
	diff .exp-factor-default.txt .obs-factor-default.txt
	smot factor prepend --default=NA fishbone.tre > .obs-factor-prepend-default.txt
	diff .exp-factor-prepend-default.txt .obs-factor-prepend-default.txt
	smot factor append --default=NA fishbone.tre > .obs-factor-append-default.txt
	diff .exp-factor-append-default.txt .obs-factor-append-default.txt
	rm .obs-*
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
	# clean up
	rm a b
