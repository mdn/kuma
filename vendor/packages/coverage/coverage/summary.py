"""Summary reporting"""

import sys

from coverage.report import Reporter
from coverage.results import Numbers


class SummaryReporter(Reporter):
    """A reporter for writing the summary report."""
    
    def __init__(self, coverage, show_missing=True, ignore_errors=False):
        super(SummaryReporter, self).__init__(coverage, ignore_errors)
        self.show_missing = show_missing
        self.branches = coverage.data.has_arcs()

    def report(self, morfs, omit_prefixes=None, outfile=None):
        """Writes a report summarizing coverage statistics per module."""
        
        self.find_code_units(morfs, omit_prefixes)

        # Prepare the formatting strings
        max_name = max([len(cu.name) for cu in self.code_units] + [5])
        fmt_name = "%%- %ds  " % max_name
        fmt_err = "%s   %s: %s\n"
        header = (fmt_name % "Name") + " Stmts   Exec"
        fmt_coverage = fmt_name + "%6d %6d"
        if self.branches:
            header += " Branch BrExec"
            fmt_coverage += " %6d %6d"
        header += "  Cover"
        fmt_coverage += " %5d%%"
        if self.show_missing:
            header += "   Missing"
            fmt_coverage += "   %s"
        rule = "-" * len(header) + "\n"
        header += "\n"
        fmt_coverage += "\n"

        if not outfile:
            outfile = sys.stdout

        # Write the header
        outfile.write(header)
        outfile.write(rule)

        total = Numbers()
        
        for cu in self.code_units:
            try:
                analysis = self.coverage._analyze(cu)
                nums = analysis.numbers
                args = (cu.name, nums.n_statements, nums.n_executed)
                if self.branches:
                    args += (nums.n_branches, nums.n_executed_branches)
                args += (nums.pc_covered,)
                if self.show_missing:
                    args += (analysis.missing_formatted(),)
                outfile.write(fmt_coverage % args)
                total += nums
            except KeyboardInterrupt:                       #pragma: no cover
                raise
            except:
                if not self.ignore_errors:
                    typ, msg = sys.exc_info()[:2]
                    outfile.write(fmt_err % (cu.name, typ.__name__, msg))

        if total.n_files > 1:
            outfile.write(rule)
            args = ("TOTAL", total.n_statements, total.n_executed)
            if self.branches:
                args += (total.n_branches, total.n_executed_branches)
            args += (total.pc_covered,)
            if self.show_missing:
                args += ("",)
            outfile.write(fmt_coverage % args)
