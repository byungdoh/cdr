import sys
import numpy as np
import math

from .util import stderr

def permutation_test(err_1, err_2, n_iter=10000, n_tails=2, mode='loss', nested=False, verbose=True):
    """
    Perform a paired permutation test for significance.

    :param err_1: ``numpy`` vector; first error/loss vector.
    :param err_2: ``numpy`` vector; second error/loss vector.
    :param n_iter: ``int``; number of resampling iterations.
    :param n_tails: ``int``; number of tails.
    :param mode: ``str``; one of ``["loss", "loglik"]``, the type of error used (losses are averaged while loglik's are summed).
    :param nested: ``bool``; assume that the second model is nested within the first.
    :param verbose: ``bool``; report progress logs to standard error.
    :return:
    """

    err_table = np.stack([err_1, err_2], 1)
    if mode == 'loss':
        base_diff = err_table[:,0].mean() - err_table[:,1].mean()
        if nested and base_diff <= 0:
            return (1.0, base_diff, np.zeros((n_iter,)))
    elif mode == 'loglik':
        base_diff = err_table[:,0].sum() - err_table[:,1].sum()
        if nested and base_diff >= 0:
            return (1.0, base_diff, np.zeros((n_iter,)))
    else:
        raise ValueError('Unrecognized aggregation function "%s" in permutation test' %mode)

    if base_diff == 0:
        return (1.0, base_diff, np.zeros((n_iter,)))

    hits = 0
    if verbose:
        stderr('Difference in test statistic: %s\n' %base_diff)
        stderr('Permutation testing...\n')

    diffs = np.zeros((n_iter,))

    for i in range(n_iter):
        if verbose:
            stderr('\r%d/%d' %(i+1, n_iter))
        shuffle = (np.random.random((len(err_table))) > 0.5).astype('int')
        m1 = err_table[np.arange(len(err_table)),shuffle]
        m2 = err_table[np.arange(len(err_table)),1-shuffle]
        if mode == 'loss':
            cur_diff = m1.mean() - m2.mean()
        else:
            cur_diff = m1.sum() - m2.sum()
        diffs[i] = cur_diff
        if n_tails == 1:
            if base_diff < 0 and cur_diff <= base_diff:
                hits += 1
            elif base_diff > 0 and cur_diff >= base_diff:
                hits += 1
        elif n_tails == 2:
            if math.fabs(cur_diff) > math.fabs(base_diff):
                hits += 1
        else:
            raise ValueError('Invalid bootstrap parameter n_tails: %s. Must be in {1, 2}.' %n_tails)

    p = float(hits+1)/(n_iter+1)

    if verbose:
        stderr('\n')

    return p, base_diff, diffs
