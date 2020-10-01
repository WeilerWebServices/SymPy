import sympy
from sympy.utilities.runtests import SymPyDocTestFinder, pdoctest, SymPyOutputChecker, SymPyDocTestRunner
from sympy.core.compatibility import StringIO
from sympy import pprint_use_unicode, init_printing
import __future__
import sys

files = [
    "introduction.tex",
    "features.tex",
    "basic_usage.tex",
    "assumptions.tex",
    "simplification.tex",
    "calculus.tex",
    "polys.tex",
    "printers.tex",
    "solvers.tex",
    "matrices.tex",
    "numerics.tex",
    "domain_specific.tex",
    "architecture.tex",
    "projects_that_depend_on_sympy.tex",

    "supplement.tex",
    "gruntz.tex",
    "series.tex",
    "logic.tex",
    "diophantine.tex",
    "sets.tex",
    "stats.tex",
    "categories.tex",
    "tensors.tex",
    "nsimplify.tex",
    "examples.tex",
    "gamma.tex",
    "comparison_with_mma.tex",
    ]

output_file = "test_full_paper.py"

begin = "\\begin{verbatim}"
end = "\\end{verbatim}"
skip = "% no-doctest\n"

def main():
    if sympy.__version__ != "1.0":
        sys.exit("The doctests must be run against SymPy 1.0. Please install SymPy 1.0 and run them again.")
    full_text = ""

    for file in files:
        with open(file, 'r') as f:
            s = f.read()
            st = s.find(begin)
            while st != -1:
                if not (st >= len(skip)) or s[st - len(skip) : st] != skip:
                    full_text += s[st + len(begin) : s.find(end, st)]
                st = s.find(begin, st+ len(begin))

    full_text = full_text.replace(r'\end{verbatim}', '')

    with open(output_file, "w") as f:
        f.write("'''\n %s \n'''" % full_text)

    # force pprint to be in ascii mode in doctests
    pprint_use_unicode(False)

    # hook our nice, hash-stable strprinter
    init_printing(pretty_print=False)

    import test_full_paper

    # find the doctest
    module = pdoctest._normalize_module(test_full_paper)
    tests = SymPyDocTestFinder().find(module)
    test = tests[0]

    runner = SymPyDocTestRunner(optionflags=pdoctest.ELLIPSIS |
            pdoctest.NORMALIZE_WHITESPACE |
            pdoctest.IGNORE_EXCEPTION_DETAIL)
    runner._checker = SymPyOutputChecker()

    old = sys.stdout
    new = StringIO()
    sys.stdout = new

    future_flags = __future__.division.compiler_flag | __future__.print_function.compiler_flag

    try:
        f, t = runner.run(test, compileflags=future_flags,
                          out=new.write, clear_globs=False)
    except KeyboardInterrupt:
        raise
    finally:
        sys.stdout = old

    if f > 0:
        print(new.getvalue())
        return 1
    else:
        return 0

if __name__ == '__main__':
    sys.exit(main())
