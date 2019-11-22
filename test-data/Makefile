# This makefile will test the expected against observed output.
# If the make command fails, then there is a problem

all:
	smot sample-proportional --paraphyletic --proportion=0.3 --min-tips=2 --factor-by-field=2 --seed=42 --keep=S fork.tre > .obs-fork.tre
	diff .obs-fork.tre .exp-fork.tre
	smot tips fishbone.tre > .obs-tips.txt
	diff .exp-tips.txt .obs-tips.txt
	smot tipsed X Y fishbone.tre > .obs-tipsed.txt
	diff .exp-tipsed.txt .obs-tipsed.txt
	smot tips fishbone.tre | smot random --seed=42 > .obs-random.txt
	diff .exp-random.txt .obs-random.txt
	smot midpoint fishbone.tre > .obs-midpoint.txt
	diff .exp-midpoint.txt .obs-midpoint.txt
	smot sample-equal --factor-by-field=2 --keep="S" --max-tips=2 --zero polytomyHS.tre > .obs-polytomyHS-equal.txt
	diff .exp-polytomyHS-equal.txt .obs-polytomyHS-equal.txt
	smot sample-proportional --seed=42 --factor-by-field=2 --proportion=0.2 --keep="S" --min-tips=2 polytomyHS.tre > .obs-polytomyHS-prop.txt
	diff .exp-polytomyHS-prop.txt .obs-polytomyHS-prop.txt
	smot sample-proportional --paraphyletic --seed=42 --factor-by-field=2 --proportion=0.2 --keep="S" --min-tips=2 polytomyHS.tre > .obs-polytomyHS-para.txt
	diff .exp-polytomyHS-para.txt .obs-polytomyHS-para.txt
	# this should randomly sample 15 taxa of th 1591 that are in H1.tre
	smot sample-proportional --proportion=0.01 --seed=42 H1.tre | smot tips > .obs-h1-hundreth-sample-prop.txt
	diff .obs-h1-hundreth-sample-prop.txt .exp-h1-hundreth-sample-prop.txt
	# this should proportionally sample while retaining all global clades and unknowns representatives 
	smot sample-proportional --proportion=0.01 --factor-by-capture='(1[ABC]\.[0-9.]*)' --seed=42 H1.tre > .obs-h1-factored-prop.tre
	diff .obs-h1-factored-prop.tre .exp-h1-factored-prop.tre
	# set default factor to NA, then list
	smot factor --default=NA fishbone.tre > .obs-factor-default.txt
	diff .exp-factor-default.txt .obs-factor-default.txt
	rm .obs-*
