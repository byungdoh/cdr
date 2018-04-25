.. _formula:

DTSR Model Formulae
===================



Basic Overview
--------------

This package constructs DTSR models from **R**-style formula strings defining the model structure.
A DTSR formula has the following template:

``RESPONSE ~ FIXED_EFFECTS + RANDOM_EFFECTS``

The left-hand side (LHS) of the formula contains the name a single (possibly transformed) variable from the input data table, and the right-hand side (RHS) contains fixed and random effects, each of which must consist exclusively of intercept terms and/or convolutional terms.
Intercept terms can be added by including ``1`` in the RHS and removed by including ``0`` in the RHS.
If neither of these appears in the RHS, an intercept is added by default.


Defining an Impulse Response Function (IRF)
-------------------------------------------

A convolutional term is defined using the syntax ``C(..., IRF_FAMILY())``, where ``...`` is replaced by names of predictors contained in the input data.
For example, to define a Gamma convolution of predictor ``A``, the expression ``C(A, Gamma())`` is added to the RHS.
Separate terms are delimited by ``+``.
For example, to add a Gaussian convolution of predictor ``B``, the RHS above becomes ``C(A, Gamma()) + C(B, Normal())``.



Supported IRF
-------------

The currently supported IRF families are:

- ``DiracDelta``: Stick function (equivalent to a predictor in linear regression)

  - Parameters: None
  - Definition: :math:`1` at :math:`x=0`, :math:`0` otherwise

- ``Exp``: PDF of exponential distribution

  - Parameters: :math:`\lambda` (rate)
  - Definition: :math:`\lambda e^{-\lambda x}`

- ``Gamma``: PDF of gamma distribution

  - Parameters: :math:`k` (shape), :math:`\theta` (rate)
  - Definition: :math:`\frac{x^{k-1}e^{-\frac{x}{\theta}}}{\theta^k\Gamma(k)}`

- ``ShiftedGamma``: PDF of gamma distribution with support starting at :math:`0 + \delta`

  - Parameters: :math:`k` (shape), :math:`\theta` (rate), :math:`\delta` (shift, strictly negative)
  - Definition: :math:`\frac{(x - \delta)^{k-1}e^{-\frac{x - \delta}{\theta}}}{\theta^k\Gamma(k)}`

- ``GammaKgt1``: PDF of gamma distribution, :math:`k > 1` (enforces rising-then-falling shape)

  - Parameters: :math:`k` (shape), :math:`\theta` (rate)
  - Definition: :math:`\frac{x^{k-1}e^{-\frac{x}{\theta}}}{\theta^k\Gamma(k)}`

- ``ShiftedGammaKgt1``: PDF of gamma distribution with support starting at :math:`0 - \delta`, :math:`k > 1` (enforces rising-then-falling shape)

  - Parameters: :math:`k` (shape), :math:`\theta` (rate), :math:`\delta` (shift, strictly negative)
  - Definition: :math:`\frac{(x - \delta)^{k-1}e^{-\frac{x - \delta}{\theta}}}{\theta^k\Gamma(k)}`

- ``Normal``: PDF of Gaussian (normal) distribution

  - Parameters: :math:`\mu` (mean), :math:`\sigma` (standard deviation)
  - Definition: :math:`\frac{1}{\sqrt{2\pi\sigma^2}}e^{-\frac{(x - \mu) ^ 2}{2 \sigma ^ 2}}`

- ``SkewNormal``: PDF of SkewNormal distribution (normal distribution augmented with left/right skew parameter)

  - Parameters: :math:`\mu` (mean), :math:`\sigma` (standard deviation), :math:`\alpha` (skew)
  - Definition: Let :math:`\phi` and :math:`\Phi` denote the PDF and CDF (respectively) of the standard normal distribution.
    Then the SkewNormal distribution is:
    :math:`\frac{2}{\sigma} \phi\left(\frac{x-\mu}{\sigma}\right) \Phi(\alpha \frac{x-\mu}{\sigma})`

- ``EMG``: PDF of exponentially modified gaussian distribution (convolution of a normal with an exponential distribution, can be right-skewed)

  - Parameters: :math:`\mu` (mean), :math:`\sigma` (standard deviation), :math:`\lambda` (rate)
  - Definition: :math:`\frac{\lambda}{2}e^{\frac{\lambda}{2}\left(2\mu + \lambda \sigma^2 - 2x \right)} \mathrm{erfc} \left(\frac{m + \lambda \sigma ^2 - x}{\sqrt{2}\sigma}\right)`, where :math:`\mathrm{erfc}(x) = \frac{2}{\sqrt{\pi}}\int_x^{\infty} e^{-t^2}dt`.

- ``BetaPrime``: PDF of BetaPrime (inverted beta) distribution

  - Parameters: :math:`\alpha` (shape), :math:`\beta` (shape)
  - Definition: :math:`\frac{x^{\alpha - 1}(1 + x)^{-\alpha - \beta}}{B(\alpha, \beta)}`

- ``ShiftedBetaPrime``: PDF of BetaPrime (inverted beta) distribution with support starting at :math:`0 + \delta`
  - Parameters: :math:`\alpha` (shape), :math:`\beta` (shape), :math:`\delta` (shift, strictly negative)
  - Definition: :math:`\frac{(x-\delta)^{\alpha - 1}(1 + (x - \delta))^{-\alpha - \beta}}{B(\alpha, \beta)}`



Automatic Term Expansion
------------------------

For convenience, the ``C()`` function distributes the impulse response family over multiple ``+``-delimited terms in its first argument.
Therefore, the following two expressions are equivalent:

``C(A + B, Gamma())``
``C(A, Gamma()) + C(B, Gamma())``

As in **R**, interaction terms are designated with ``:``, as in ``C(A:B, Gamma())``, and cross-product interactions can be expressed using Python's power notation ``**<INT>``.
For example, ``(A + B + C)**3`` adds all first, second, and third order interactions, expanding out as:

``A + B + C + A:B + B:C + A:C + A:B:C``

As above, IRF distribute across the expansion of interaction terms, such that the following expressions are equivalent:

``C((A + B + C)**3, Gamma())``
``C(A, Gamma()) + C(B, Gamma()) + C(C, Gamma()) + C(A:B, Gamma()) + C(B:C, Gamma()) + C(A:C, Gamma()) + C(A:B:C, Gamma())``

Unlike **R**, categorical variables are not yet handled automatically in DTSR.
However, they can be included simply by adding binary indicator vectors for each of :math:`n-1` of the levels of the variable to the input data as a preprocessing step, then defining the model in terms of the binary indicators.

Note that the term expansions described above add `separate` IRF for each term in the expansion.
For example, ``C(A + B, Gamma())`` adds two distinct Gamma IRF parameterizations to the model, one for each predictor.
It is also possible to tie IRF between predictor variables (details below).

Note also that (unlike **R**) redundant terms are **not** automatically collapsed, so care must be taken to ensure that no duplicate terms are produced via term expansion.


Random Effects
--------------

Random effects in DTSR are specified using the following syntax:

``(RANDOM_TERMS | GROUPING_FACTOR)``

where ``RANDOM_TERMS`` are terms as they would appear in the RHS of the model described above and ``GROUPING_FACTOR`` is the name of a categorical variable in the input that is used to define the random effect (e.g. a vector of ID's of human subjects).
As in the case of fixed effects, a random intercept is automatically added unless ``0`` appears among the random terms.
Mixed models are constructed simply by adding random effects to fixed effects in the RHS of the formula.
For example, to construct a mixed model with a fixed and by-subject random coefficient for a Gaussian IRF for predictor ``A`` along with a random intercept by subject, the following RHS would be used:

``C(A, Normal()) + (C(A, Normal()) | subject)``

IRF in random effects statements are treated as tied to any corresponding fixed effects unless explicitly distinguished by distinct IRF ID's (see section below on parameter tying).

The above formula uses a single parameterization for the Gaussian IRF and fits by-subject coefficients for it.
However it is also possible to fit by-subject IRF parameterizations.
This can be accomplished by adding ``ran=T`` to the IRF call, as shown below:

``C(A, Normal()) + (C(A, Normal(ran=T)) | subject)``

This formula will fit separate coefficients `and` IRF shapes for this predictor for each subject.

An important complication in fitting mixed models with DTSR is that the relevant grouping factor is determined by the current `regression target`, not the properties of the independent variable observations in the series history.
This means that random effects are only guaranteed to be meaningful when fit using grouping factors that are constant for the entire series (e.g. the ID of the human subject completing the experiment).
Random effects fit for grouping factors that vary during the experiment should therefore be avoided unless they are intercept terms only, which are not affected by the temporal convolution.




Parameter Tying
---------------

A convolutional term in a DTSR model is factored into two components, an IRF component with appropriate parameters and a coefficient governing the overall amplitude of the estimate.
Unless otherwise specified, both of these terms are fit separately for every predictor in the model.
However, parameter tying is possible by passing keyword arguments to the IRF calls in the model formula.
Coefficients can be tied using the ``coef_id`` argument, and IRF parameters can be tied using the ``irf_id`` argument.
For example, the following RHS fits separate IRF and coefficients for each of ``A`` and ``B``:

``C(A, Normal()) + C(B, Normal())``

The following fits a single IRF (called "IRF_NAME") but separate coefficients for ``A`` and ``B``:

``C(A, Normal(irf_id=IRF_NAME)) + C(B, Normal(irf_id=IRF_NAME))``

The following fits separate IRF but a single coefficient (called "COEF_NAME") for both ``A`` and ``B``:

``C(A, Normal(coef_id=COEF_NAME)) + C(B, Normal(coef_id=COEF_NAME))``

And the following fits a single IRF (called "IRF_NAME") and a single coefficient (called "COEF_NAME"), both of which are shared between ``A`` and ``B``:

``C(A, Normal(irf_id=IRF_NAME, coef_id=COEF_NAME)) + C(B, Normal(irf_id=IRF_NAME, coef_id=COEF_NAME))``






Transforming Variables
----------------------
DTSR provides limited support for automatic variable transformations based on model formulae.
As in **R** formulae, a transformation is applied by wrapping the predictor name in the transformation function.
For example, to fit a Gamma IRF to a log transform of predictor ``A``, the following is added to the RHS:

``C(log(A), Gamma())``

Transformations may be applied to the predictors and/or the response.

The following are the currently supported transformations:

- ``log()``: Applies a natural logarithm transformation to the variable
- ``log1p()``: Adds 1 to the variable an applies a natural logarithm transformation (useful if predictor can include 0)
- ``exp()``: Exponentiates the variable
- ``z()``: Z-transforms the variable (subtracts its mean and divides by its standard deviation)
- ``c()``: 0-centers the variable (subtracts its mean)
- ``s()``: Scales the variable (divides by its standard deviation)

Other transformations must be applied via data preprocessing.




Planned Features (Future Work)
------------------------------

- **Continuous inputs**: The current DTSR model is only valid for discrete input signals.
  Input signals that constitute `samples` from a continuous source signal cannot be convolved exactly because the source is generally not analytically integrable.
  Research is ongoing into computationally efficient methods for approximating the convolution integral for samples from a continuous signal.
  When implemented, continuous variables will be able to be specified in the formula using the ``cont=T`` keyword argument in the IRF call.
- **Hierarchical convolution**: Composing convolutions using distinct IRF, as in ``Exp(Normal())``, i.e. first convolving with a Gaussian IRF, then convolving the output of the first convolution with an Exponential IRF.
  Research is ongoing into computationally efficient methods to fit these more complex convolutions functions.