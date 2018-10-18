# -*- coding: utf-8 -*-

#  shortrate
#  -----------
#  risk factor model library python style.
#
#  Author:  pbrisk <pbrisk_at_github@icloud.com>
#  Website: https://github.com/pbrisk/shortrate
#  License: MIT (see LICENSE file)

from businessdate import BusinessDate, BusinessRange
from dcf import ZeroRateCurve, FxCurve
from timewave import Consumer, Engine


from shortrate.risk_factor_model import RiskFactorProducer
from shortrate.market_risk_factor import GBMFxCurve, GeometricBrownianMotionRiskFactorModel, \
    Price, GeometricBrownianMotionPrice, GeometricBrownianMotionFxRate
from shortrate.hullwhite_model import HullWhiteCurve, HullWhiteCurveFactorModel
from shortrate.hullwhite_multicurrency_model import HullWhiteFxCurve, HullWhiteMultiCurrencyCurve

from test import MultiCcyHullWhiteSimulationUnitTests, HullWhiteSimulationUnitTests, _try_plot


def do_test(m, t):

    c = m(t)
    c.setUp()
    getattr(c, t)()
    c.tearDown()

if 1:
    s, t = BusinessDate(), BusinessDate() + '10y'

    g = GeometricBrownianMotionPrice(value=1.2, origin=s, volatility=.1)#, start=1.1)
    print g, g.inner_factor
    print 'mu', g.drift(10), 'sigma', g.volatility(2), 'start', g.start
    for q in range(10):
        q = float(q)*.1
        g.evolve_risk_factor(g.start, s, t, -q)
        print q, g.value,
        g.evolve_risk_factor(g.start, s, t, q)
        print g.value, g._factor_date
    print g, g.inner_factor
    print ''

    g = GeometricBrownianMotionFxRate(value=1.2, origin=s, volatility=.1)#, start=1.1)
    print g, g.inner_factor
    print 'mu', g.drift(10), 'sigma', g.volatility(2), 'start', g.start
    for q in range(10):
        q = float(q)*.1
        g.evolve_risk_factor(g.start, s, t, -q)
        print q, g.value,
        g.evolve_risk_factor(g.start, s, t, q)
        print g.value, g._factor_date
    print g, g.inner_factor
    print ''

if 1:
    s = BusinessDate()
    t = s + '10y'
    g = BusinessRange(s, t, '6M')
    d = ZeroRateCurve([s], [0.05])
    f = ZeroRateCurve([s], [0.04])
    x = FxCurve([s], [.8], domestic_curve=d, foreign_curve=f)
    r = GBMFxCurve.build(x, volatility=0.2)

    print repr(r), repr(r.inner_factor)

    print r.evolve(1., s, s + '1y', 0.01)
    print r.get_fx_rate(s + '3y'), r._factor_date
    print r.evolve(1., s + '1y', s + '5y', 0.1)
    print r.get_fx_rate(s + '7y'), r._factor_date

    print repr(r), repr(r.inner_factor)
    print ''

    hwd = HullWhiteCurve.build(d, mean_reversion=0.01, volatility=0.03, terminal_date=t)
    hwf = HullWhiteCurveFactorModel(f, mean_reversion=0.01, volatility=0.03, terminal_date=t)
    hwx = HullWhiteFxCurve.build(r, hwd, hwf)
    hwxf = HullWhiteMultiCurrencyCurve.build(hwf, hwd, hwx)

    print repr(hwd), repr(hwd.inner_factor)
    print repr(hwf), repr(hwf.inner_factor)
    print repr(hwxf), repr(hwxf.inner_factor)

    print hwd.evolve(1., s, s + '1y', 0.01)
    print hwf.evolve(1., s, s + '1y', 0.02)
    print hwx.evolve(1., s, s + '1y', (0.01, 0.02, 0.01))
    print hwxf.evolve(1., s, s + '1y', 0.02)

    print repr(hwd), repr(hwd.inner_factor)
    print repr(hwf), repr(hwf.inner_factor)
    print repr(hwxf), repr(hwxf.inner_factor)
    print ''


    # func = (lambda x: hwd.get_discount_factor(x, t) * hwd.get_discount_factor(s, x))
    func = (lambda x: hwd.get_cash_rate(t - '1y'))
    c = Consumer(lambda x: func(x.date))
    # res = Engine(RiskFactorProducer(hwd), c).run(g, 100)
    # _try_plot({'test': res}, g)

if 0:
    do_test(MultiCcyHullWhiteSimulationUnitTests, 'test_simulation')
    # do_test(HullWhiteSimulationUnitTests, 'test_multi_simulation')