# -*- coding: utf-8 -*-

#  shortrate
#  -----------
#  risk factor model library python style.
#
#  Author:  pbrisk <pbrisk_at_github@icloud.com>
#  Website: https://github.com/pbrisk/shortrate
#  License: MIT (see LICENSE file)

from datetime import datetime
from os import getcwd, sep, path, makedirs
from unittest import TestCase, main

from businessdate import BusinessDate, BusinessRange
from dcf import ZeroRateCurve, DiscountFactorCurve, FxCurve

from shortrate.risk_factor_model import RiskFactorProducer, MultiRiskFactorProducer
from shortrate.hullwhite_model import HullWhiteCurve
from shortrate.hullwhite_multicurrency_model import HullWhiteMultiCurrencyCurve, HullWhiteFxCurve, GBMFxCurve

from timewave import Engine, ConsumerConsumer, Consumer, MultiConsumer, StatisticsConsumer

p = '.' + sep + 'pdf'
if not path.exists(p):
    makedirs('.' + sep + 'pdf')


class ValuationConsumer(StatisticsConsumer):
    """Consumer calling valuation function with state.date argument"""

    def __init__(self, valuation_func):
        super(ValuationConsumer, self).__init__(lambda s: valuation_func(s.date))

    def finalize(self):
        """finalize for ValuationConsumer"""
        super(ValuationConsumer, self).finalize()
        self.result = [r.mean for p, r in self.result]


def _try_plot(plot, grid, today=None):
    if today is None:
        today = grid[0]
    try:
        import matplotlib.pyplot as plt
        g = [today.diff_in_years(d) for d in grid]
        for k in plot:
            # print 'plot:', k
            for l in plot[k]:
                plt.plot(g, l)
            n = float(len(plot[k]))
            t = map(list, zip(*plot[k]))
            plt.plot(g, [sum(l)/n for l in t], 'k.')
            plt.title(k)
            # plt.ylim(0.2, 1.0)
            plt.savefig('.' + sep + 'pdf' + sep + k + '.pdf')
            # plt.show()
            plt.close()
    except ImportError:
        pass


_today = BusinessDate(20171231)
_grid = BusinessRange(_today, _today + '10y', step='3m')
_term = [-.0100, 0.0005, 0.0079, 0.0131, 0.0164, 0.0184, 0.0195, 0.0198,
         0.0197, 0.0192, 0.0185, 0.0176, 0.0167, 0.0157, 0.0147, 0.0137,
         0.0127, 0.0118, 0.0109, 0.0100, 0.0092, 0.0084, 0.0077, 0.0070,
         0.0064, 0.0058, 0.0052, 0.0047, 0.0042, 0.0037, 0.0033, 0.0029,
         0.0025, 0.0021, 0.0018, 0.0014, 0.0011, 0.0008, 0.0005, 0.0003, -.0000]


class HullWhiteModelUnitTests(TestCase):
    def setUp(self):
        self.today = _today
        self.grid = _grid
        self.termday = self.grid[-1]
        self.flat_zero_curve = ZeroRateCurve([self.today], [0.05])
        self.term_zero_curve = ZeroRateCurve(self.grid, _term)
        self.zero_curve = self.flat_zero_curve
        self.mean_reversion = .1
        self.volatility = .005
        self.hull_white_curve = HullWhiteCurve.cast(self.zero_curve,
                                                    mean_reversion=self.mean_reversion,
                                                    volatility=self.volatility)

        self.plot = dict()

    def tearDown(self):
        if __name__ == '__main__':
            _try_plot(self.plot, self.grid, self.today)

    def test_integrals(self):
        s = self.today.diff_in_years(self.today)
        tau_grid = [self.today.diff_in_years(d) for d in self.grid]
        for a in ['calc_integral_B', 'calc_integral_I1', 'calc_integral_I1_squared',
                  'calc_integral_volatility_squared_with_I1', 'calc_integral_volatility_squared_with_I1_squared',
                  'calc_integral_I2']:
            f = getattr(self.hull_white_curve, a)
            value_list = [f(s, d) for d in tau_grid]
            self.plot[a] = [value_list]


class HullWhiteCurveUnitTests(TestCase):
    def setUp(self):
        self.today = _today
        self.grid = _grid
        self.termday = self.grid[-1]
        self.flat_zero_curve = ZeroRateCurve([self.today], [0.05])
        self.term_zero_curve = ZeroRateCurve(self.grid, _term)
        self.zero_curve = self.flat_zero_curve
        self.mean_reversion = .1
        self.volatility = .005
        self.hull_white_curve = HullWhiteCurve.cast(self.zero_curve,
                                                    mean_reversion=self.mean_reversion,
                                                    volatility=self.volatility)
        self.plot = dict()

    def tearDown(self):
        if __name__ == '__main__':
            _try_plot(self.plot, self.grid, self.today)

    def test_curve(self):
        for d in self.grid:
            assert self.zero_curve.get_discount_factor(self.today, d) == \
                   self.hull_white_curve.get_discount_factor(self.today, d), \
                'HullWhiteCurve fails at get_discount_factor(self.today, d) = get_discount_factor(%s, %s)' \
                % (str(self.today), str(d))
            assert self.zero_curve.get_discount_factor(d, self.termday) == \
                   self.hull_white_curve.get_discount_factor(d, self.termday), \
                'HullWhiteCurve fails at get_discount_factor(d, self.termday) = get_discount_factor(%s, %s)' \
                % (str(d), str(self.termday))
            if not self.today == d and not d == self.termday:
                assert self.zero_curve.get_zero_rate(self.today, d) == self.hull_white_curve.get_zero_rate(self.today,
                                                                                                           d), \
                    'HullWhiteCurve fails at get_zero_rate(self.today, d) = get_zero_rate(%s, %s)' \
                    % (str(self.today), str(d))
                assert self.zero_curve.get_zero_rate(d, self.termday) == \
                       self.hull_white_curve.get_zero_rate(d, self.termday), \
                    'HullWhiteCurve fails at get_zero_rate(d, self.termday) = get_zero_rate(%s, %s)' \
                    % (str(d), str(self.termday))
            assert self.zero_curve.get_cash_rate(d) == self.hull_white_curve.get_cash_rate(d), \
                'HullWhiteCurve fails at get_cash_rate(d) = get_cash_rate(%s)' \
                % (str(d))

    def test_short_rate(self):
        res = list()
        res.append([self.hull_white_curve.get_zero_rate(self.today, t) for t in self.grid])
        for short_rate in [-.01, .0, .01]:
            self.hull_white_curve.set_risk_factor(self.today, short_rate)
            res.append([self.hull_white_curve.get_zero_rate(self.today, t) for t in self.grid])
            res.append([self.hull_white_curve.get_cash_rate(t) for t in self.grid])
        self.plot['test_short_rate'] = res
        self.assertTrue(True)

    def test_forward_rate(self):
        res = list()
        res.append([self.hull_white_curve.get_zero_rate(self.today, t) for t in self.grid])
        for short_rate in [-.01, .0, .01]:
            for p in ['0d', '1y', '2y', '3y']:
                self.hull_white_curve.set_risk_factor(self.today + p, short_rate)
                res.append([self.hull_white_curve.get_zero_rate(self.today, t) for t in self.grid])
        self.plot['test_forward_rate'] = res
        self.assertTrue(True)

    def test_mean_reversion(self):
        res = list()
        res.append([self.hull_white_curve.get_zero_rate(self.today, t) for t in self.grid])
        for short_rate in [-.01, .0, .01]:
            for mr in [0.01, 0.02, 0.05, 0.1, 0.2, 0.5]:
                hwc = HullWhiteCurve.cast(self.zero_curve, mean_reversion=mr, volatility=self.volatility)
                hwc.set_risk_factor(self.today + '1y', short_rate)
                res.append([hwc.get_zero_rate(self.today, t) for t in self.grid])
        self.plot['test_mean_reversion'] = res
        self.assertTrue(True)

    def test_volatility(self):
        res = list()
        res.append([self.hull_white_curve.get_zero_rate(self.today, t) for t in self.grid])
        for short_rate in [-.01, .0, .01]:
            for v in [.005, .01, .05, .1]:
                hwc = HullWhiteCurve.cast(self.zero_curve, mean_reversion=self.mean_reversion, volatility=v)
                hwc.set_risk_factor(self.today + '1y', short_rate)
                res.append([hwc.get_zero_rate(self.today, t) for t in self.grid])
        self.plot['test_volatility'] = res
        self.assertTrue(True)


class HullWhiteSimulationUnitTests(TestCase):
    def setUp(self):
        self.today = _today
        self.grid = _grid
        self.termday = self.grid[-1]
        self.flat_zero_curve = ZeroRateCurve([self.today], [0.05])
        self.term_zero_curve = ZeroRateCurve(self.grid, _term)
        self.zero_curve = self.flat_zero_curve
        self.mean_reversion = .1
        self.volatility = .005
        self.hull_white_curve = HullWhiteCurve.cast(self.zero_curve,
                                                    mean_reversion=self.mean_reversion,
                                                    volatility=self.volatility)

        self.df_func = (lambda x: self.hull_white_curve.get_discount_factor(x, self.termday) *
                                  self.hull_white_curve.inner_factor.get_discount_factor(self.today, self.termday) /
                                  self.hull_white_curve.inner_factor.get_discount_factor(x, self.termday))
        self.fw_func = (lambda x: self.hull_white_curve.get_cash_rate(self.termday - '1y'))

        self.num_of_paths = 100
        self.plot = dict()

    def tearDown(self):
        _try_plot(self.plot, self.grid, self.today)

    def test_simulation(self):
        # setup timewave framework
        producer = RiskFactorProducer(self.hull_white_curve)
        x_consumer = Consumer(lambda x: x.value)
        df_consumer = Consumer(lambda x: self.df_func(x.date))
        pv_consumer = ValuationConsumer(self.df_func)
        fw_consumer = Consumer(lambda x: self.fw_func(x.date))
        af_consumer = ValuationConsumer(self.fw_func)

        consumer = ConsumerConsumer([x_consumer, df_consumer, pv_consumer, fw_consumer, af_consumer])

        # run the simulation
        x, df_sim, df_avg, fwd_sim, fwd_avg = Engine(producer, consumer).run(self.grid, self.num_of_paths)

        # self.plot['state_avg'] = [[sum(xx) / len(xx) for xx in map(list, zip(*x))]]
        # self.plot['state_path'] = x

        self.plot['libor_avg'] = [fwd_avg, [self.zero_curve.get_cash_rate(d) for d in self.grid]]
        self.plot['libor_path'] = fwd_sim

        self.plot['df_avg'] = [df_avg,
                               [self.zero_curve.get_discount_factor(self.today, self.termday) for d in self.grid]]
        self.plot['df_path'] = df_sim

        dfc = DiscountFactorCurve(self.grid, df_avg)
        self.plot['zero_avg'] = [[dfc.get_zero_rate(self.today, d) for d in self.grid],
                                 [self.zero_curve.get_zero_rate(self.today, d) for d in self.grid]]
        zr_list = list()
        for dfs in df_sim:
            dfc = DiscountFactorCurve(self.grid, dfs)
            zr_list.append([dfc.get_zero_rate(self.today, d) for d in self.grid])
        self.plot['zero_path'] = zr_list

    def test_single_hull_white_model(self):
        producer = RiskFactorProducer(self.hull_white_curve)
        consumer = Consumer()
        result = Engine(producer, consumer).run(self.grid, self.num_of_paths)
        self.plot['single rf hull white'] = result

    def test_multi_hull_white_model(self):
        producer = MultiRiskFactorProducer([self.hull_white_curve])
        consumer = MultiConsumer(Consumer())
        result = Engine(producer, consumer).run(self.grid, self.num_of_paths)
        self.plot['multi rf hull white'] = result[0]

    def test_multi_simulation(self):

        res = list()
        for vol in [.005, .01]:
            for mr in [0.01, 0.1]:
                hwc = HullWhiteCurve.cast(self.zero_curve, mean_reversion=mr, volatility=vol)
                func = (lambda x: hwc.get_discount_factor(x, self.termday) *
                                  hwc.get_discount_factor(self.today, x))
                func = (lambda x: hwc.get_cash_rate(self.termday - '1y'))
                producer = RiskFactorProducer(hwc)
                fs_consumer = Consumer(lambda x: func(x.date))
                avg_consumer = ValuationConsumer(func)

                consumer = ConsumerConsumer([fs_consumer, avg_consumer])

                # run the simulation
                fs, avg = Engine(producer, consumer).run(self.grid, self.num_of_paths)
                res.append(avg)
                self.plot['func sample v: %0.3f mr: %0.3f ' % (vol, mr)] = fs

        self.plot['func avg'] = res


class MultiCcyHullWhiteSimulationUnitTests(TestCase):
    def setUp(self):
        self.today = _today
        self.grid = _grid
        self.termday = self.grid[-1]
        self.flat_zero_curve = ZeroRateCurve([self.today], [0.05])
        self.term_zero_curve = ZeroRateCurve(self.grid, _term)
        self.zero_curve = self.flat_zero_curve
        self.fx_curve = FxCurve([self.today], [1.], domestic_curve=self.zero_curve, foreign_curve=self.zero_curve)
        self.fx_volatility = .3
        self.gbm_fx_curve = GBMFxCurve.cast(self.fx_curve, self.fx_volatility)
        self.mean_reversion = .1
        self.volatility = .005
        self.hull_white_curve = HullWhiteCurve.cast(self.zero_curve,
                                                    mean_reversion=self.mean_reversion,
                                                    volatility=self.volatility)
        self.hull_white_curve_2 = HullWhiteCurve.cast(ZeroRateCurve([self.today], [0.03]),
                                                      mean_reversion=self.mean_reversion*2,
                                                      volatility=self.volatility*0.5)
        self.df_func = (lambda x: self.hull_white_curve.get_discount_factor(x, self.termday) *
                                  self.hull_white_curve.inner_factor.get_discount_factor(self.today, self.termday) /
                                  self.hull_white_curve.inner_factor.get_discount_factor(x, self.termday))
        self.fw_func = (lambda x: self.hull_white_curve.get_cash_rate(self.termday - '1y'))

        self.num_of_paths = 100
        self.plot = dict()

    def tearDown(self):
        _try_plot(self.plot, self.grid, self.today)

    def test_simulation(self):
        # setup timewave framework
        corr = dict()
        corr_list = list()
        corr_list.append((.0, .0, .0))
        corr_list.append((-.2, -.5, .7))
        corr_list.append((.2, .5, .7))
        corr_list.append((.2, .5, -.3))
        corr_list.append((-.2, .5, -.3))
        for dx, fx, df in corr_list:
            corr[self.hull_white_curve, self.gbm_fx_curve] = dx
            corr[self.hull_white_curve_2, self.gbm_fx_curve] = fx
            corr[self.hull_white_curve, self.hull_white_curve_2] = df
            hull_white_fx_curve = HullWhiteFxCurve.cast(self.gbm_fx_curve,
                                                        self.hull_white_curve,
                                                        self.hull_white_curve_2, None, corr)

            hull_white_mc_curve = HullWhiteMultiCurrencyCurve.cast(self.hull_white_curve_2,
                                                                   self.hull_white_curve,
                                                                   hull_white_fx_curve)

            factors = [self.hull_white_curve, hull_white_mc_curve, hull_white_fx_curve]
            # build producer
            producer = MultiRiskFactorProducer(factors, corr)
            # for fact in factors:
            #     print repr(fact) , repr(fact.diffusion_driver)
            # for k, v in producer._driver_index.iteritems():
            #     print repr(k.process), v
            # build consumer
            consumer = MultiConsumer(Consumer(), Consumer(), Consumer())
            # run engine
            result = Engine(producer, consumer).run(self.grid, self.num_of_paths)
            c = repr((dx, fx, df))
            self.plot['multi hull white d corr=%s' %c] = result[0]
            self.plot['multi hull white f corr=%s' %c] = result[1]
            self.plot['multi hull white x corr=%s' %c] = result[2]


if __name__ == "__main__":
    start_time = datetime.now()

    print('')
    print('======================================================================')
    print('')
    print('run %s' % __file__)
    print('in %s' % getcwd())
    print('started  at %s' % str(start_time))
    print('')
    print('----------------------------------------------------------------------')
    print('')

    main(verbosity=2)

    print('')
    print('======================================================================')
    print('')
    print('ran %s' % __file__)
    print('in %s' % getcwd())
    print('started  at %s' % str(start_time))
    print('finished at %s' % str(datetime.now()))
    print('')
    print('----------------------------------------------------------------------')
    print('')
