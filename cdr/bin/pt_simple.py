import sys
import os
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

from cdr.config import Config
from cdr.signif import permutation_test, correlation_test
from cdr.util import filter_models, get_partition_list, nested, stderr


def scale(a):
    return (a - a.mean()) / a.std()


if __name__ == '__main__':
    argparser = argparse.ArgumentParser('''
        Tests error/likelihood measures of prediction quality between two sets of predictions (most likely generated by two different models).
    ''')
    argparser.add_argument('df1_path', help='Path to first set of predictions')
    argparser.add_argument('df2_path', help='Path to second set of predictions')
    argparser.add_argument('-T', '--tails', type=int, default=2, help='Number of tails (1 or 2)')
    args, unknown = argparser.parse_known_args()

    df1_path = args.df1_path
    df2_path = args.df2_path

    if df1_path.startswith('losses_mse') or df1_path.startswith('squared_error'):
        metric = 'err'
    elif df1_path.startswith('loglik'):
        metric = 'loglik'
    else:
        raise ValueError('Unrecognized error file %s' % df1_path)
    a = pd.read_csv(df1_path, sep=' ', header=None, skipinitialspace=True)
    b = pd.read_csv(df1_path, sep=' ', header=None, skipinitialspace=True)
    select = np.logical_and(np.isfinite(np.array(a)), np.isfinite(np.array(b)))
    diff = float(len(a) - select.sum())
    p_value, base_diff, diffs = permutation_test(
        a[select],
        b[select],
        n_iter=10000,
        n_tails=args.tails,
        mode=metric,
        nested=False
    )
    stderr('\n')

    summary = '=' * 50 + '\n'
    summary += 'Model comparison:'
    summary += 'Path 1: %s\n' % df1_path
    summary += 'Path 2: %s\n' % df2_path
    if diff > 0:
        summary += '%d NaN rows filtered out (out of %d)\n' % (diff, len(a))
    summary += 'Metric: %s\n' % metric
    summary += 'Difference: %.4f\n' % base_diff
    summary += 'p: %.4e%s\n' % (
    p_value, '' if p_value > 0.05 else '*' if p_value > 0.01 else '**' if p_value > 0.001 else '***')
    summary += '=' * 50 + '\n'

    sys.stdout.write(summary)
