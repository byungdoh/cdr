.. _getting_started:

Getting Started
===============

The ``cdr`` package provides utilities that support easy training and evaluation of CDR models.
Most of these utilities depend on a config file ``*.ini`` containing metadata needed to construct the CDR model(s).
At training time, a copy of the config file is placed in the output directory for the experiment, which can be useful for record keeping.
The approach of using config files rather than command line arguments to define experiments has several advantages:

- Users only need to define the experiment once, and settings can be reused for arbitrarily many models
- The config file contains a permanent record of the settings used in the experiment, facilitating later reproduction
- The config file can be shared across many utilities (training, evaluation, statistical testing, plotting, etc.)

This guide describes how to write the config file and use it to train and evaluate CDR models.




Configuring CDR Experiments
----------------------------

A set of CDR experiments is definied in a config file ``*.ini``, which can then be passed to CDR executables.
For example, once a config file ``foo.ini`` has been created, the models defined in it can be trained using the included ``train`` executable, like so:::

    python -m cdr.bin.train foo.ini

The config file must at minimum contain the sections ``[data]`` (with pointers to training/evaluation data), ``[global_settings]`` (with the location of the output directory) and ``[cdr_settings]`` (with arguments used to construct the model).
In addition, the config file should contain at least one model section, consisting of the prefix ``model_CDR_`` followed by a custom name for the model.
For example, to define a CDR model called ``readingtimes``, use the section heading ``[model_CDR_readingtimes]``.
The identifier ``CDR_readingtimes`` will then be used by a number of utilities to designate this model
(the reason ``CDR`` must be included in the prefix is that this repository distributes with unofficial support for running LM, LME, and GAM models from the same interface).
The data and settings configurations will be shared between all models defined a single config file.
Each model section heading should contain at least the field ``formula``.
The value provided to ``formula`` must be a valid CDR model string.
Additional fields may be provided to override inherited CDR settings on a model-specific basis.
Experiments involving distinct datasets require distinct config files.

For more details on the available configuration parameters, see :ref:`config`.
For more details on CDR model formulae, see :ref:`formula`.



Running CDR executables
------------------------

A number of executable utilities are contained in the module ``cdr.bin`` and can be executed using Python's ``-m`` flag.
For example, the following call runs the ``train`` utility on all models specified in a config file ``config.ini``:::

    python -m cdr.bin.train config.ini

Usage help for each utility can be viewed by running:::

    python -m cdr.bin.<UTIL-NAME> -h

for the utility in question.
Or usage help for all utilities can be printed at once using:::

    python -m cdr.bin.help

The following sections go into more detail about training and evaluation utilities that will likely be useful to most users.




Training CDR Models
--------------------

First, gather some data and write a config file defining your experiments.
Note that CDR utilities assume the data will be saved in a **space-delimited text file**, a requirement that facilitates interoperability with the [Modelblocks repository](https://github.com/modelblocks/modelblocks-release), which can be used to generate and preprocess data for many psycholinguistic experiments.
Once the config file has been written, training a CDR model is simple using the ``train`` utility, which takes as its principle argument a path to the config file.
For example, if the config file is names ``experiment.ini``, all models defined in it can be trained with the call:::

    python -m dstr.bin.train experiment.ini

To restrict training to some subset of models, the ``-m`` flag is used.
For example, the following call trains models ``A`` and ``B`` only:::

    python -m cdr.bin.train experiment.ini -m CDR_A CDR_B

CDR periodically saves training checkpoints to the model's output directory (every **save_freq** training epochs, where **save_freq** can be defined in the config file or left at its default of ``1``).
This allows training to be interrupted and resumed.
To save space, checkpoints overwrite each other, so the output directory will contain only the most recent checkpoint.
If the ``train`` utility discovers a checkpoint in the model's output directory, it loads it and resumes training from the saved state.
This feature can also be used to add training epochs after termination in the event of model non-convergence.
Simply increase the number of training iterations specified in the config file and rerun ``train``, and the model will continue training until it hits the new maximum number of epochs.

It is strongly encouraged to monitor changes in the parameters via Tensorboard in order to visually diagnose convergence.
When parameters do not seem to have moved substantially over the course of the most recent training epochs, training can be terminated.
This is important because in practice overall training loss may decrease very little during the final stages of training while the model fine-tunes IRF shapes, so Tensorboard diagnostics are more informative for convergence than overall loss.
To run Tensorboard for a CDR model called ``CDR_A`` saved in experiment directory ``EXP``, run::

    python -m tensorboard.main --logdir=EXP/CDR_A

then open the returned address (usually ``http://<USERNAME>:6006``) in a web browser.

Evaluating CDR Models
----------------------

This package provides several utilities for inspecting and evaluating fitted CDR models.
The principal evaluation utility is ``predict``.
The following generates predictions on test data from the model ``CDR_A`` defined in ``experiment.ini``:::

    python -m cdr.bin.predict experiment.ini -m CDR_A -p test

This call will save files containing elementwise predictions, errors, and likelihoods, along with a performance summary.
For more details on usage, run:::

    python -m cdr.bin.predict -h

Once ``predict`` has been run for multiple models, statistical model comparison (permutation test) can be performed using ``compare``, as shown:::

    python -m cdr.bin.compare experiment.ini -p test

The above call will permutation test pairwise differences in mean squared error on test data for all unique pairs of models defined in ``experiment.ini``.

In addition to these core utilities, ``convolve`` convolves the input predictors using the fitted CDR data transform and saves the data table, and ``make_plots`` generates IRF plots with basic customization as permitted by the command line arguments.




