

First setup basic objects
=========================

first import module

.. code-block:: python

    from shortrate import HullWhiteCurve



then set up basic instance

.. code-block:: python

    x = HullWhiteCurve.build(zero_curve=zc,
                            mean_reversion=mr,
                            volatility=vol,
                            terminal_date=grid[-1])
