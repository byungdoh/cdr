from __future__ import print_function
import sys
import re
import pickle
import numpy as np
from scipy import linalg


def stderr(s):
    sys.stderr.write(s)
    sys.stderr.flush()

def names2ix(names, l, dtype=np.int32):
    """
    Generate 1D numpy array of indices in **l** corresponding to names in **names**

    :param names: ``list`` of ``str``; names to look up in **l**
    :param l: ``list`` of ``str``; list of names from which to extract indices
    :param dtype: ``numpy`` dtype object; return dtype
    :return: ``numpy`` array; indices of **names** in **l**
    """

    if type(names) is not list:
        names = [names]
    ix = []
    for n in names:
        ix.append(l.index(n))
    return np.array(ix, dtype=dtype)


def mse(true, preds):
    """
    Compute mean squared error (MSE).

    :param true: True values
    :param preds: Predicted values
    :return: ``float``; MSE
    """

    return ((true-preds)**2).mean()


def mae(true, preds):
    """
    Compute mean absolute error (MAE).

    :param true: True values
    :param preds: Predicted values
    :return: ``float``; MAE
    """

    return (true-preds).abs().mean()


def percent_variance_explained(true, preds):
    """
    Compute percent variance explained.

    :param true: True values
    :param preds: Predicted values
    :return: ``float``; percent variance explained
    """

    num = mse(true, preds)
    denom = np.std(true) ** 2
    return max(0., (1 - num / denom) * 100)


def get_random_permutation(n):
    """
    Draw a random permutation of integers 0 to **n**.
    Used to shuffle arrays of length **n**.
    For example, a permutation and its inverse can be generated by calling ``p, p_inv = get_random_permutation(n)``.
    To randomly shuffle an **n**-dimensional vector ``x``, call ``x[p]``.
    To un-shuffle ``x`` after it has already been shuffled, call ``x[p_inv]``.

    :param n: maximum value
    :return: 2-tuple of ``numpy`` arrays; the permutation and its inverse
    """

    p = np.random.permutation(np.arange(n))
    p_inv = np.zeros_like(p)
    p_inv[p] = np.arange(n)
    return p, p_inv


def sn(string):
    """
    Compute a Tensorboard-compatible version of a string.

    :param string: ``str``; input string
    :return: ``str``; transformed string
    """

    return re.sub('[^A-Za-z0-9_.\\-/]', '.', string)


def reg_name(string):
    """
    Standardize a variable name for regularization

    :param string: ``str``; input string
    :return: ``str``; transformed string
    """

    name = string.split(':')[0]
    name = name.replace('/', '_')
    cap = True
    var_name = ''
    for c in name:
        if c == '_':
            cap = True
        else:
            if cap:
                var_name += c.upper()
            else:
                var_name += c
            cap = False

    return var_name


def pca(X, n_dim=None, dtype=np.float32):
    """
    Perform principal components analysis on a data table.

    :param X: ``numpy`` or ``pandas`` array; the input data
    :param n_dim: ``int`` or ``None``; maximum number of principal components. If ``None``, all components are retained.
    :param dtype: ``numpy`` dtype; return dtype
    :return: 5-tuple of ``numpy`` arrays; transformed data, eigenvectors, eigenvalues, input means, and input standard deviations
    """

    X = np.array(X, dtype=dtype)
    assert len(X.shape) == 2, 'Wrong dimensionality for PCA (X must be rank 2).'
    means = X.mean(0, keepdims=True)
    sds = X.std(0, keepdims=True)
    X -= means
    X /= sds
    C = np.cov(X, rowvar=False)
    eigenval, eigenvec = linalg.eigh(C)
    sorted_id = np.argsort(eigenval)[::-1]
    eigenval = eigenval[sorted_id]
    eigenvec = eigenvec[:,sorted_id]
    if n_dim is not None and n_dim < eigenvec.shape[1]:
        eigenvec = eigenvec[:,:n_dim]
    Xpc = np.dot(X, eigenvec)
    return Xpc, eigenvec, eigenval, means, sds


def nested(model_name_1, model_name_2):
    """
    Check whether two CDR models are nested with 1 degree of freedom

    :param model_name_1: ``str``; name of first model
    :param model_name_2: ``str``; name of second model
    :return: ``bool``; ``True`` if models are nested with 1 degree of freedom, ``False`` otherwise
    """
    split = (model_name_1.split('!'), model_name_2.split('!'))
    m_base = [x[0] for x in split]
    m_ablated = [set(x[1:]) for x in split]
    a = 0 if len(m_ablated[0]) < len(m_ablated[1]) else 1
    b = 1 - a

    return m_base[a] == m_base[b] and len(m_ablated[b] - m_ablated[a]) == 1 and len(m_ablated[a] - m_ablated[b]) == 0


def filter_names(names, filters):
    """
    Return elements of **names** permitted by **filters**, preserving order in which filters were matched.
    Filters can be ordinary strings, regular expression objects, or string representations of regular expressions.
    For a regex filter to be considered a match, the expression must entirely match the name.

    :param names: ``list`` of ``str``; pool of names to filter.
    :param filters: ``list`` of ``{str, SRE_Pattern}``; filters to apply in order
    :return: ``list`` of ``str``; names in **names** that pass at least one filter
    """

    filters_regex = [re.compile(f if f.endswith('$') else f + '$') for f in filters]

    out = []

    for i in range(len(filters)):
        filter = filters[i]
        filter_regex = filters_regex[i]
        for name in names:
            if name not in out:
                if name == filter:
                    out.append(name)
                elif filter_regex.match(name):
                    out.append(name)

    return out


def filter_models(names, filters, cdr_only=False):
    """
    Return models contained in **names** that are permitted by **filters**, preserving order in which filters were matched.
    Filters can be ordinary strings, regular expression objects, or string representations of regular expressions.
    For a regex filter to be considered a match, the expression must entirely match the name.
    If ``filters`` is zero-length, returns **names**.

    :param names: ``list`` of ``str``; pool of model names to filter.
    :param filters: ``list`` of ``{str, SRE_Pattern}``; filters to apply in order
    :param cdr_only: ``bool``; if ``True``, only returns CDR models. If ``False``, returns all models admitted by **filters**.
    :return: ``list`` of ``str``; names in **names** that pass at least one filter, or all of **names** if no filters are applied.
    """

    if cdr_only:
        names = [name for name in names if (name.startswith('CDR') or name.startswith('DTSR'))]

    if len(filters) > 0:
        out = filter_names(names, filters)
    else:
        out = names
    return out


def get_partition_list(partition):
    if not isinstance(partition, list):
        partition = partition.strip().split()
    if len(partition) == 1:
        partition = partition[0].split('-')
    if len(partition) == 1:
        partition = partition[0].split('+')
    return partition


def paths_from_partition_cliarg(partition, config):
    partition = get_partition_list(partition)
    X_paths = []
    y_paths = []

    X_map = {
        'train': config.X_train,
        'dev': config.X_dev,
        'test': config.X_test
    }

    y_map = {
        'train': config.y_train,
        'dev': config.y_dev,
        'test': config.y_test
    }

    for p in partition:
        X_path = X_map[p]
        y_path = y_map[p]

        if X_path not in X_paths:
            X_paths.append(X_path)
        if y_path not in y_paths:
            y_paths.append(y_path)

    return X_paths, y_paths


def get_irf_name(x, irf_name_map):
    for y in sorted(list(irf_name_map.keys())):
        if y in x:
            return irf_name_map[y]
    return x



def load_cdr(dir_path):
    """
    Convenience method for reconstructing a saved CDR object. First loads in metadata from ``m.obj``, then uses
    that metadata to construct the computation graph. Then, if saved weights are found, these are loaded into the
    graph.

    :param dir_path: Path to directory containing the CDR checkpoint files.
    :return: The loaded CDR instance.
    """

    with open(dir_path + '/m.obj', 'rb') as f:
        m = pickle.load(f)
    m.build(outdir=dir_path)
    m.load(outdir=dir_path)
    return m