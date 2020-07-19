import logging
import re
from collections import OrderedDict, defaultdict

from dvc.repo import locked
from dvc.repo.metrics.show import _collect_metrics, _read_metrics
from dvc.repo.params.show import _collect_configs, _read_params

logger = logging.getLogger(__name__)


EXP_RE = re.compile(r"(?P<rev_sha>[a-f0-9]{7})-(?P<exp_sha>[a-f0-9]+)")


def _collect_experiment(repo, branch):
    res = defaultdict(dict)
    for rev in repo.brancher(revs=[branch]):
        configs = _collect_configs(repo)
        params = _read_params(repo, configs, rev)
        if params:
            res["params"] = params

        metrics = _collect_metrics(repo, None, False)
        vals = _read_metrics(repo, metrics, rev)
        if vals:
            res["metrics"] = vals

    return res


@locked
def show(
    repo, all_branches=False, all_tags=False, revs=None, all_commits=False
):
    res = defaultdict(OrderedDict)

    if revs is None:
        revs = [repo.scm.get_rev()]

    revs = set(
        repo.brancher(
            revs=revs,
            all_branches=all_branches,
            all_tags=all_tags,
            all_commits=all_commits,
        )
    )

    for rev in revs:
        res[rev]["baseline"] = _collect_experiment(repo, rev)

    for exp_branch in repo.experiments.scm.list_branches():
        m = re.match(EXP_RE, exp_branch)
        if m:
            rev = repo.scm.resolve_rev(m.group("rev_sha"))
            if rev in revs:
                exp_rev = repo.experiments.scm.resolve_rev(exp_branch)
                with repo.experiments.chdir():
                    experiment = _collect_experiment(
                        repo.experiments.exp_dvc, exp_branch
                    )
                res[rev][exp_rev] = experiment

    return res