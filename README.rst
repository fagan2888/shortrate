=========
shortrate
=========

.. image:: https://img.shields.io/codeship/c1455c20-9d70-0134-6c98-327be1016a00/master.svg
    :target: https://codeship.com//projects/188651

risk factor model library python style.


Example Usage
-------------

.. code-block:: python

    from businessdate import BusinessDate, BusinessRange
    from dcf import ZeroRateCurve, FxCurve
    from timewave import Consumer, Engine

    from shortrate import RiskFactorProducer, GBMFxCurve, HullWhiteCurve, HullWhiteFxCurve, HullWhiteMultiCurrencyCurve

    s = BusinessDate()
    t = s + '10y'
    g = BusinessRange(s, t, '6M')
    d = ZeroRateCurve([s], [0.05])
    f = ZeroRateCurve([s], [0.04])
    x = FxCurve([s], [.8], domestic_curve=d, foreign_curve=f)
    r = GBMFxCurve.cast(x, volatility=0.2)

    print r.evolve(1., s, s + '1y', 0.01)
    print r.get_fx_rate(s + '3y'), r._factor_date
    print r.evolve(1., s + '1y', s + '5y', 0.1)
    print r.get_fx_rate(s + '7y'), r._factor_date

    hwd = HullWhiteCurve.cast(d, mean_reversion=0.01, volatility=0.03, terminal_date=t)
    hwf = HullWhiteCurve.cast(f, mean_reversion=0.01, volatility=0.03, terminal_date=t)
    hwx = HullWhiteFxCurve.cast(r, hwd, hwf)
    hwxf = HullWhiteMultiCurrencyCurve.cast(hwf, hwd, hwx)

    print hwd.evolve(1., s, s + '1y', 0.01)
    print hwf.evolve(1., s, s + '1y', 0.02)
    print hwx.evolve(1., s, s + '1y', (0.01, 0.02, 0.01))
    print hwxf.evolve(1., s, s + '1y', 0.02)

    func = (lambda x: hwd.get_cash_rate(t - '1y'))
    c = Consumer(lambda x: func(x.date))
    res = Engine(RiskFactorProducer(hwd), c).run(g, 100)

    print res

Install
-------

The latest stable version can always be installed or updated via pip:

.. code-block:: bash

    $ pip install shortrate

If the above fails, please try easy_install instead:

.. code-block:: bash

    $ easy_install shortrate


Development Version
-------------------

The latest development version can be installed directly from GitHub:

.. code-block:: bash

    $ pip install --upgrade git+https://github.com/pbrisk/shortrate.git


Contributions
-------------

.. _issues: https://github.com/pbrisk/shortrate/issues
.. __: https://github.com/pbrisk/shortrate/pulls

Issues_ and `Pull Requests`__ are always welcome.


License
-------

.. __: https://github.com/pbrisk/shortrate/raw/master/LICENSE

Code and documentation are available according to the Apache Software License (see LICENSE__).


