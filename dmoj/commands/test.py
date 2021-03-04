import sys
import traceback
from operator import itemgetter

from dmoj.commands.base_command import Command
from dmoj.error import InvalidCommandException
from dmoj.judgeenv import get_problem_root, get_supported_problems
from dmoj.problem import ProblemConfig, ProblemDataManager
from dmoj.testsuite import Tester
from dmoj.utils.ansi import ansi_style, print_ansi


class ProblemTester(Tester):
    def test_problem(self, problem_id):
        self.output(ansi_style('Testing problem #ansi[%s](cyan|bold)...') % problem_id)

        config = ProblemConfig(ProblemDataManager(get_problem_root(problem_id)))

        if not config or 'tests' not in config or not config['tests']:
            self.output(ansi_style('\t#ansi[Skipped](magenta|bold) - No tests found'))

        fails = 0
        for test in config['tests']:
            # Do this check here as we need some way to identify the test
            if 'source' not in test:
                self.output(ansi_style('\t[Skipped](magenta|bold) - No source found for test'))
                continue

            test_name = test.get('label', test['source'])
            self.output(ansi_style('\tRunning test #ansi[%s](yellow|bold)') % test_name)
            try:
                test_fails = self.run_test(problem_id, test)
            except Exception:
                fails += 1
                self.output(ansi_style('\t#ansi[Test failed with exception:](red|bold)'))
                self.output(traceback.format_exc())
            else:
                self.output(ansi_style('\tResult of test #ansi[%s](yellow|bold): ') % test_name +
                            ansi_style(['#ansi[Failed](red|bold)', '#ansi[Success](green|bold)'][not test_fails]))
                fails += test_fails

        return fails

    def _check_targets(targets):
        if 'posix' in targets:
            return True
        if 'freebsd' in sys.platform:
            if 'freebsd' in targets:
                return True
            if not sys.platform.startswith('freebsd') and 'kfreebsd' in targets:
                return True
        elif sys.platform.startswith('linux') and 'linux' in targets:
            return True
        return False

    def run_test(self, problem_id, config):
        if 'targets' in config and not self._check_targets(config['targets']):
            return 0

        return self._run_test_case(problem_id, get_problem_root(problem_id), config)


class TestCommand(Command):
    name = 'test'
    help = 'Runs tests on a problem.'

    def _populate_parser(self):
        self.arg_parser.add_argument('problem_id', help='id of problem to test')

    def execute(self, line):
        args = self.arg_parser.parse_args(line)

        problem_id = args.problem_id

        if problem_id not in map(itemgetter(0), get_supported_problems()):
            raise InvalidCommandException("unknown problem '%s'" % problem_id)

        tester = ProblemTester()
        fails = tester.test_problem(problem_id)
        print()
        print('Test complete')
        if fails:
            print_ansi('#ansi[A total of %d test(s) failed](red|bold)' % fails)
        else:
            print_ansi('#ansi[All tests passed.](green|bold)')

        return fails
