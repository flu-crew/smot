# This makefile will test the expected against observed output.
# If the make command fails, then there is a problem

all:
	jon sample-proportional --paraphyletic --proportion=0.5 --min-tips=2 --factor-by-field=2 --seed=42 fork.tre > fork-obs.tre
	diff fork-obs.tre fork-exp.tre
	rm fork-obs.tre
