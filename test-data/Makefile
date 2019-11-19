# This makefile will test the expected against observed output.
# If the make command fails, then there is a problem

all:
	../smot.py sample-proportional --paraphyletic --proportion=0.3 --min-tips=2 --factor-by-field=2 --seed=42 --keep=S fork.tre > fork-obs.tre
	diff fork-obs.tre fork-exp.tre
	rm fork-obs.tre
