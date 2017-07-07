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
from shortrate.market_risk_factor import GBMFxCurve
from shortrate.hullwhite_model import HullWhiteCurve
from shortrate.hullwhite_multicurrency_model import HullWhiteFxCurve, HullWhiteMultiCurrencyCurve

from test import MultiCcyHullWhiteSimulationUnitTests, HullWhiteSimulationUnitTests, _try_plot

def do_test(m, t):

    c = m(t)
    c.setUp()
    getattr(c, t)()
    c.tearDown()

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

# func = (lambda x: hwd.get_discount_factor(x, t) * hwd.get_discount_factor(s, x))
func = (lambda x: hwd.get_cash_rate(t - '1y'))
c = Consumer(lambda x: func(x.date))
# res = Engine(RiskFactorProducer(hwd), c).run(g, 100)
# _try_plot({'test': res}, g)

do_test(MultiCcyHullWhiteSimulationUnitTests, 'test_simulation')
# do_test(HullWhiteSimulationUnitTests, 'test_multi_simulation')