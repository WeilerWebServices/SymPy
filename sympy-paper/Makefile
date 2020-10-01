all: authors.tex pprint.pdf paper.pdf supplement.pdf rebuttal.pdf rebuttal2.pdf

paper.pdf: paper.tex authors.tex introduction.tex architecture.tex features.tex assumptions.tex basic_usage.tex simplification.tex numerics.tex domain_specific.tex projects_that_depend_on_sympy.tex conclusion_and_future_work.tex siamart0216_uppercase_fix.tex pprint.pdf pprint.tex printers.tex calculus.tex matrices.tex solvers.tex images/fig1-circuitplot-qft.pdf paper.bib wlpeerj.cls supplement.pdf
	pdflatex -shell-escape --halt-on-error paper.tex
	bibtex paper.aux
	pdflatex -shell-escape --halt-on-error paper.tex
	pdflatex -shell-escape --halt-on-error paper.tex

.PHONY: diff
diff: paper-diff.pdf supplement-diff.pdf

paper-diff.tex: supplement.pdf paper.pdf diff.xsh
	./diff.xsh PeerJ-version-4-resubmit

supplement-diff.pdf: paper-diff.tex supplement-diff.bbl
	pdflatex -shell-escape --halt-on-error supplement-diff.tex
	pdflatex -shell-escape --halt-on-error supplement-diff.tex
	pdflatex -shell-escape --halt-on-error supplement-diff.tex

paper-diff.pdf: paper-diff.tex
	pdflatex -shell-escape --halt-on-error paper-diff.tex
	pdflatex -shell-escape --halt-on-error paper-diff.tex
	pdflatex -shell-escape --halt-on-error paper-diff.tex

supplement.pdf: categories.tex comparison_with_mma.tex diophantine.tex examples.tex gamma.tex gruntz.tex logic.tex nsimplify.tex polys.tex series.tex sets.tex stats.tex supplement.tex tensors.tex paper.bib images/supp-fig2-integral_steps.png wlpeerj.cls
	pdflatex -shell-escape --halt-on-error supplement.tex
	bibtex supplement
	pdflatex -shell-escape --halt-on-error supplement.tex
	pdflatex -shell-escape --halt-on-error supplement.tex

rebuttal.pdf: rebuttal.tex coverletter.pdf
	pdflatex -shell-escape --halt-on-error rebuttal.tex
	pdflatex -shell-escape --halt-on-error rebuttal.tex

rebuttal2.pdf: rebuttal2.tex coverletter2.pdf
	pdflatex -shell-escape --halt-on-error rebuttal2.tex
	pdflatex -shell-escape --halt-on-error rebuttal2.tex

coverletter.pdf: coverletter.tex
	pdflatex -shell-escape --halt-on-error coverletter.tex
	pdflatex -shell-escape --halt-on-error coverletter.tex

coverletter2.pdf: coverletter2.tex
	pdflatex -shell-escape --halt-on-error coverletter2.tex
	pdflatex -shell-escape --halt-on-error coverletter2.tex

authors.tex: authors/list_latex.py authors/authors.json
	cd authors; ./list_latex.py

pprint.pdf: pprint.tex
	xelatex --halt-on-error pprint.tex

.PHONY: test
test:
	python test-paper.py

.PHONY: clean
clean:
	(rm -rf *.ps *.log *.dvi *.aux *.*% *.lof *.lop *.lot *.toc *.idx *.ilg *.ind *.bbl *.blg *.cpt *-diff.tex *.out)
	(rm -rf authors.tex pprint.pdf paper.pdf supplement.pdf rebuttal.pdf coverletter.pdf coverletter2.pdf rebuttal2.pdf paper-diff.pdf supplement-diff.pdf)
	(rm -rf __pycache__ test_full_paper.py)
