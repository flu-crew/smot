# This makefile will test the expected against observed output.
# If the make command fails, then there is a problem

all:
	smot sample-proportional --paraphyletic --proportion=0.3 --min-tips=2 --factor-by-field=2 --seed=42 --keep=S fork.tre > fork-obs.tre
	diff fork-obs.tre fork-exp.tre
	rm fork-obs.tre
	smot tips fishbone.tre > obs-tips.txt
	diff exp-tips.txt obs-tips.txt
	smot tipsed X Y fishbone.tre > obs-tipsed.txt
	diff exp-tipsed.txt obs-tipsed.txt
	smot tips fishbone.tre | smot random --seed=42 > obs-random.txt
	diff exp-random.txt obs-random.txt
	smot midpoint fishbone.tre > obs-midpoint.txt
	diff exp-midpoint.txt obs-midpoint.txt
	smot sample-equal --factor-by-field=2 --keep="S" --max-tips=2 --zero polytomyHS.tre > obs-polytomyHS-equal.txt
	diff exp-polytomyHS-equal.txt obs-polytomyHS-equal.txt
	smot sample-proportional --seed=42 --factor-by-field=2 --proportion=0.2 --keep="S" --min-tips=2 polytomyHS.tre > obs-polytomyHS-prop.txt
	diff exp-polytomyHS-prop.txt obs-polytomyHS-prop.txt
	smot sample-proportional --paraphyletic --seed=42 --factor-by-field=2 --proportion=0.2 --keep="S" --min-tips=2 polytomyHS.tre > obs-polytomyHS-para.txt
	diff exp-polytomyHS-para.txt obs-polytomyHS-para.txt
