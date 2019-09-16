# -*- coding: utf-8 -*-

# shortrate
# ---------
# risk factor model library python style.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.3, copyright Saturday, 14 September 2019
# Website:  https://github.com/sonntagsgesicht/shortrate
# License:  Apache License 2.0 (see LICENSE file)

from __future__ import print_function


import sys
import matplotlib
from math import exp, log, sqrt

sys.path.append('.')
sys.path.append('test')
matplotlib.use('agg')

from businessdate import BusinessDate, BusinessRange
from dcf import ZeroRateCurve, continuous_compounding
from timewave import Consumer, Engine, TransposedConsumer, StatisticsConsumer
from timewave.stochasticconsumer import _BootstrapStatistics
from putcall import black_scholes, black, forward_black_scholes

from shortrate.risk_factor_model import RiskFactorProducer, _OptionStatistics
from shortrate.market_risk_factor import GeometricBrownianMotionPrice, GeometricBrownianMotionFxRate
from shortrate.hullwhite_model import HullWhiteCurve, HullWhiteCurveFactorModel
from shortrate.hullwhite_multicurrency_model import HullWhiteMultiCurrencyCurveFactorModel, HullWhiteFxRateFactorModel

from unittests import MultiCcyHullWhiteSimulationUnitTests, HullWhiteSimulationUnitTests, _try_plot

if 0:
    start, end = BusinessDate(20181231), BusinessDate(20191231)  # , BusinessDate(20200101)
    rate, vol = 0.05, 0.2

    process = GeometricBrownianMotionPrice(value=1., origin=start, drift=rate - 0.5 * (vol ** 2), volatility=vol)
    r = Engine(RiskFactorProducer(process), Consumer()).run(grid=[start, end],
                                                            num_of_workers=None,
                                                            num_of_paths=int(1e5))

if 1:
    from random import Random

    num, multi, seed = 10000, None, Random().randint(0, 10)
    rate, vol = 0.05, 0.2
    drift = rate - 0.5 * (vol ** 2)
    price, strike = 1., 1.
    start, end = BusinessDate(), BusinessDate() + '1y'  # , BusinessDate(20200101)

    process = GeometricBrownianMotionPrice(value=price, origin=start, drift=drift, volatility=vol,
                                           day_count=BusinessDate.get_day_count)
    time = process.day_count(start, end)  # 0.999315537303
    df = continuous_compounding(rate, time)

    sc = StatisticsConsumer(statistics=_OptionStatistics, strike=strike, process=process, description=str(process),
                            call=forward_black_scholes(price / df, strike, vol, time, True),
                            put=forward_black_scholes(price / df, strike, vol, time, False))
    stat = Engine(RiskFactorProducer(process), sc).run(grid=[start, end], num_of_paths=num)[-1][-1]

    mc = stat.call, stat.put
    bs = black_scholes(price, strike, vol, time, True, rate) / df, \
         black_scholes(price, strike, vol, time, False, rate) / df
    bk = black(price / df, strike, vol, time, True), \
         black(price / df, strike, vol, time, False)
    fw = forward_black_scholes(price / df, strike, vol, time, True),\
         forward_black_scholes(price / df, strike, vol, time, False)

    print('start', price, 'strike', strike, 'time', time, end=' ')
    print('rate', rate, 'vol', vol, 'drift', drift)
    print('')
    print('                                 call        put')
    print('analytical Black Scholes         %0.8f, %0.8f' % bs)
    print('analytical forward Black Scholes %0.8f, %0.8f' % fw)
    print('analytical Black76               %0.8f, %0.8f' % bk)
    print('simulation Monte Carlo           %0.8f, %0.8f' % mc)
    print('')
    print(stat)

    if False:
        print('')
        stat = _BootstrapStatistics(stat.sample, process=process, time=time)
        stat.description = str(process)
        print(stat)
        print(list(stat.values()))

if 0:
    s, t = BusinessDate(), BusinessDate() + '10y'

    g = GeometricBrownianMotionPrice(value=1.2, origin=s, volatility=.1)  # , start=1.1)
    print(g, g.inner_factor)
    print('mu', g.drift(10), 'sigma', g.volatility(2), 'start', g.start)
    for q in range(10):
        q = float(q) * .1
        g.evolve_risk_factor(g.start, s, t, -q)
        print(q, g.value, end=' ')
        g.evolve_risk_factor(g.start, s, t, q)
        print(g.value, g._factor_date)
    print(g, g.inner_factor)
    print('')

    g = GeometricBrownianMotionFxRate(value=1.2, origin=s, volatility=.1)  # , start=1.1)
    print(g, g.inner_factor)
    print('mu', g.drift(10), 'sigma', g.volatility(2), 'start', g.start)
    for q in range(10):
        q = float(q) * .1
        g.evolve_risk_factor(g.start, s, t, -q)
        print(q, g.value, end=' ')
        g.evolve_risk_factor(g.start, s, t, q)
        print(g.value, g._factor_date)
    print(g, g.inner_factor)
    print('')

if 0:
    s = BusinessDate()
    t = s + '10y'
    g = BusinessRange(s, t, '6M')
    d = ZeroRateCurve([s], [0.05])
    f = ZeroRateCurve([s], [0.04])
    r = GeometricBrownianMotionFxRate(0.8, s, volatility=0.2)

    print(r, r.inner_factor)

    print(r.evolve_risk_factor(1., s, s + '1y', 0.01))
    print(r.value, r._factor_date)
    print(r.evolve_risk_factor(1., s + '1y', s + '5y', 0.1))
    print(r.value, r._factor_date)

    print(r, r.inner_factor)
    r.set_risk_factor()
    print(r, r.inner_factor)
    print('')

    hwd = HullWhiteCurve([s], [0.05], mean_reversion=0.01, volatility=0.03, terminal_date=t)
    hwf = HullWhiteCurveFactorModel(f, mean_reversion=0.01, volatility=0.03, terminal_date=t)
    hwx = HullWhiteFxRateFactorModel(r, hwd, hwf)
    hwxf = HullWhiteMultiCurrencyCurveFactorModel(hwf, hwd, hwx)

    print(repr(hwd), repr(hwd.inner_factor))
    print(repr(hwf), repr(hwf.inner_factor))
    print(repr(hwxf), repr(hwxf.inner_factor))

    print(hwd.evolve(1., s, s + '1y', 0.01))
    print(hwf.evolve(1., s, s + '1y', 0.02))
    print(hwx.evolve(1., s, s + '1y', (0.01, 0.02, 0.01)))
    print(hwxf.evolve(1., s, s + '1y', 0.02))

    print(repr(hwd), repr(hwd.inner_factor))
    print(repr(hwf), repr(hwf.inner_factor))
    print(repr(hwxf), repr(hwxf.inner_factor))
    print('')

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
