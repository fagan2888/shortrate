# -*- coding: utf-8 -*-

#  shortrate
#  -----------
#  risk factor model library python style.
#
#  Author:  pbrisk <pbrisk_at_github@icloud.com>
#  Website: https://github.com/pbrisk/shortrate
#  License: MIT (see LICENSE file)

from math import exp

from businessdate import BusinessDate, BusinessRange
from dcf import ZeroRateCurve, continuous_compounding
from timewave import Consumer, Engine, TransposedConsumer, StatisticsConsumer, ConsumerConsumer
from putcall import black_scholes, black, forward_black_scholes

from shortrate.risk_factor_model import RiskFactorProducer
from shortrate.market_risk_factor import GeometricBrownianMotionPrice, GeometricBrownianMotionFxRate
from shortrate.hullwhite_model import HullWhiteCurve, HullWhiteCurveFactorModel
from shortrate.hullwhite_multicurrency_model import HullWhiteMultiCurrencyCurveFactorModel, HullWhiteFxRateFactorModel

from test import MultiCcyHullWhiteSimulationUnitTests, HullWhiteSimulationUnitTests, _try_plot


if 1:
    num, multi, seed = 10000, 4, 5
    rate, vol = 0.0, 0.1
    price, strike = 1., 1.
    start, end = BusinessDate(), BusinessDate() + '1y'

    process = GeometricBrownianMotionPrice(value=price, origin=start, drift=rate, volatility=vol)

    time = process.day_count(start, end)
    forward = price / continuous_compounding(rate, time)
    forward = price * exp((rate + 0.5 * vol ** 2) * time)
    print 'BS', forward, black_scholes(price, strike, vol, time, True, rate)
    print 'FB', forward, forward_black_scholes(forward, strike, vol, time, True)
    print 'BK', forward, black(forward, strike, vol, time, True)
    c = ConsumerConsumer(TransposedConsumer(), StatisticsConsumer())
    sample, stat = Engine(RiskFactorProducer(process), c).run(grid=[start, end], seed=seed,
                                                              num_of_paths=num, num_of_workers=multi)

    avg = (lambda x: sum(x)/len(sample[-1]))
    print 'MC', avg(sample[-1]), avg(map((lambda x: max(x-strike, 0)), sample[-1]))
    print ''
    print stat[-1][-1]
    # print stat[-1][-1].box

if 0:
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

if 0:
    s = BusinessDate()
    t = s + '10y'
    g = BusinessRange(s, t, '6M')
    d = ZeroRateCurve([s], [0.05])
    f = ZeroRateCurve([s], [0.04])
    r = GeometricBrownianMotionFxRate(0.8, s, volatility=0.2)

    print r, r.inner_factor

    print r.evolve_risk_factor(1., s, s + '1y', 0.01)
    print r.value, r._factor_date
    print r.evolve_risk_factor(1., s + '1y', s + '5y', 0.1)
    print r.value, r._factor_date

    print r, r.inner_factor
    r.set_risk_factor()
    print r, r.inner_factor
    print ''

    hwd = HullWhiteCurve([s], [0.05], mean_reversion=0.01, volatility=0.03, terminal_date=t)
    hwf = HullWhiteCurveFactorModel(f, mean_reversion=0.01, volatility=0.03, terminal_date=t)
    hwx = HullWhiteFxRateFactorModel(r, hwd, hwf)
    hwxf = HullWhiteMultiCurrencyCurveFactorModel(hwf, hwd, hwx)

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
    def do_test(m, t):
        c = m(t)
        c.setUp()
        getattr(c, t)()
        c.tearDown()

    do_test(MultiCcyHullWhiteSimulationUnitTests, 'test_simulation')
    # do_test(HullWhiteSimulationUnitTests, 'test_multi_simulation')