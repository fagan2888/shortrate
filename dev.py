# -*- coding: utf-8 -*-

#  shortrate
#  -----------
#  risk factor model library python style.
#
#  Author:  pbrisk <pbrisk_at_github@icloud.com>
#  Website: https://github.com/pbrisk/shortrate
#  License: MIT (see LICENSE file)

from math import exp, log, sqrt

from businessdate import BusinessDate, BusinessRange
from dcf import ZeroRateCurve, continuous_compounding
from timewave import Consumer, Engine, TransposedConsumer, StatisticsConsumer
from timewave.stochasticconsumer import _BootstrapStatistics
from putcall import black_scholes, black, forward_black_scholes

from shortrate.risk_factor_model import RiskFactorProducer
from shortrate.market_risk_factor import GeometricBrownianMotionPrice, GeometricBrownianMotionFxRate
from shortrate.hullwhite_model import HullWhiteCurve, HullWhiteCurveFactorModel
from shortrate.hullwhite_multicurrency_model import HullWhiteMultiCurrencyCurveFactorModel, HullWhiteFxRateFactorModel

from test import MultiCcyHullWhiteSimulationUnitTests, HullWhiteSimulationUnitTests, _try_plot

if 0:
    process = GeometricBrownianMotionPrice(value=1., origin=BusinessDate(20181231), drift=0.1, volatility=0.2)
    Engine(RiskFactorProducer(process), Consumer()).run(grid=[process.origin, process.origin + '1y'],
                                                        num_of_workers=None, num_of_paths=int(1e5))

if 1:
    from random import Random

    num, multi, seed = 100000, None, Random().randint(0, 10)
    rate, vol = 0.05, 0.2
    drift = rate - 0.5 * (vol ** 2)
    price, strike = 1., 1.05
    start, end = BusinessDate(20181231), BusinessDate(20191231)  # , BusinessDate(20200101)

    process = GeometricBrownianMotionPrice(value=price, origin=start, drift=drift, volatility=vol,
                                           day_count=BusinessDate.get_act_act)
    time = process.day_count(start, end)  # 0.999315537303
    df = continuous_compounding(rate, time)

    e = Engine(RiskFactorProducer(process), StatisticsConsumer(process=process, description=str(process)))
    # todo  code _OptionStatistics ?
    stat = e.run(grid=[start, end], seed=seed, num_of_paths=num)[-1][-1]
    call = (lambda s, k: sum(map((lambda x: max(x - k, 0)), s)) / num * df)
    mc = call(stat.sample, strike)

    bs = black_scholes(price, strike, vol, time, True, rate)
    bl = black(price / df, strike, vol, time, True)
    fw = forward_black_scholes(price / df, strike, vol, time, True)
    print bs, bl * df, fw * df

    print 'start', price, 'strike', strike,
    print 'rate', rate, 'vol', vol, 'drift', drift
    print process, 'time', time
    print stat
    print 'bs call  :     ', mc, '-', bs, '=', mc - bs, '(', (mc / bs - 1.) * 100, '%)'
    assert abs((mc / bs) - 1.) < 0.01

    if False:
        print ''
        stat = _BootstrapStatistics(stat.sample, process=process, time=time)
        stat.description = str(process)
        print stat
        print stat.values()

if 0:
    s, t = BusinessDate(), BusinessDate() + '10y'

    g = GeometricBrownianMotionPrice(value=1.2, origin=s, volatility=.1)  # , start=1.1)
    print g, g.inner_factor
    print 'mu', g.drift(10), 'sigma', g.volatility(2), 'start', g.start
    for q in range(10):
        q = float(q) * .1
        g.evolve_risk_factor(g.start, s, t, -q)
        print q, g.value,
        g.evolve_risk_factor(g.start, s, t, q)
        print g.value, g._factor_date
    print g, g.inner_factor
    print ''

    g = GeometricBrownianMotionFxRate(value=1.2, origin=s, volatility=.1)  # , start=1.1)
    print g, g.inner_factor
    print 'mu', g.drift(10), 'sigma', g.volatility(2), 'start', g.start
    for q in range(10):
        q = float(q) * .1
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
