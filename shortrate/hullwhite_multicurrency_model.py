# -*- coding: utf-8 -*-

#  shortrate
#  -----------
#  risk factor model library python style.
#
#  Author:  sonntagsgesicht <sonntagsgesicht@github.com>
#  Website: https://github.com/sonntagsgesicht/shortrate
#  License: MIT (see LICENSE file)


from math import exp

from scipy import integrate

from businessdate import BusinessDate
from dcf import FxCurve, ZeroRateCurve

from risk_factor_model import RiskFactorModel
from market_risk_factor import GBMFxCurve
from hullwhite_model import HullWhiteCurve


class HullWhiteMultiCurrencyCurve(HullWhiteCurve):
    @classmethod  # todo align signature with HullWhiteFxCurve ???
    def cast(cls, foreign_curve, domestic_curve, fx_curve):
        """
        :param HullWhiteCurve foreign_curve:
        :param HullWhiteCurve domestic_curve:
        :param HullWhiteFxCurve fx_curve:
        :return HullWhiteMultiCurrencyCurve:

        build HullWhiteMultiCurrencyCurve from HullWhiteCurves and HullWhiteFxCurve.
        Terminal measure date in foreign_curve is ignored since it is taken from domestic_curve.
        """

        new = cls(inner_factor=foreign_curve,
                  domestic_curve=domestic_curve,
                  fx_curve=fx_curve,
                  foreign_correlation=fx_curve.foreign_correlation,
                  rate_correlation=fx_curve.rate_correlation)
        return new

    def __init__(self, x_list=None, y_list=None, y_inter=None,
                 origin=None, day_count=None, forward_tenor=None,
                 mean_reversion=0.0001, volatility=0.0,
                 domestic_curve=None, fx_curve=None,
                 foreign_correlation=0.0, rate_correlation=0.0,
                 inner_factor=None):

        """
            initializes foreign Hull White curve in multi currency model

        :param list(float) x_list:
        :param list(float) y_list:
        :param list(interpolation) y_inter:
        :param BusinessDate origin:
        :param DayCount day_count:
        :param BusinessPeriod forward_tenor:
        :param float or function mean_reversion: volatility of foreign short rate process
        :param float or function volatility: volatility of foreign short rate process
        :param HullWhiteCurve domestic_curve: domestic rate HullWhite process
        :param HullWhiteFxCurve or GBMFxCurve fx_curve: fx curve with volatility of ln(fx) process
        :param float foreign_correlation: correlation of ln(fx) process and foreign rate process
        :param float rate_correlation: correlation of domestic rate process and foreign rate process
        :param RateCurve inner_factor:
        """
        terminal_date = domestic_curve.terminal_date if domestic_curve else None

        if inner_factor is None:
            inner_factor = ZeroRateCurve(x_list, y_list, y_inter, origin, day_count, forward_tenor)
        else:
            if any([x_list, y_list, y_inter, origin, day_count, forward_tenor]):
                raise (TypeError, 'If `inner_factor` is given all other `RateCurve` properties must be `None`.')
            if isinstance(inner_factor, HullWhiteCurve):
                mean_reversion = inner_factor.mean_reversion
                volatility = inner_factor.volatility
                terminal_date = inner_factor.terminal_date

        RiskFactorModel.__init__(self, inner_factor, 0.0)

        super(HullWhiteMultiCurrencyCurve, self).__init__(inner_factor=inner_factor,
                                                          mean_reversion=mean_reversion,
                                                          volatility=volatility,
                                                          terminal_date=terminal_date)
        # init volatility
        fx_volatility = fx_curve.volatility
        if isinstance(fx_volatility, float):
            self._fx_volatility = (lambda x: fx_volatility)
        elif hasattr(fx_volatility, 'origin'):
            self._fx_volatility = fx_volatility.to_curve()
        else:
            self._fx_volatility = fx_volatility

        self._domestic_model = domestic_curve if domestic_curve else self.inner_factor
        self._fx_model = fx_curve
        self._foreign_correlation = foreign_correlation
        self._rate_correlation = rate_correlation

        if isinstance(self.inner_factor, RiskFactorModel):
            self._diffusion_driver = self.inner_factor
        else:
            self._diffusion_driver = self

    # integration helpers

    def calc_integral_I2(self, s, t):
        r"""
        calculates the following integral (see formula for the step in the MC evolution)

        .. math:: \textrm{Var}(\chi(t) | \mathcal{F}_s) = \int_s^t \sigma^2_d(u)B^2_d(u, T) +
         \sigma^2_f(u)B^2_f(u,T) + \sigma^2_{FX}(u) \\
         + 2\left(- \rho_{d,f} B_f(u, T)\sigma_f(u)B_d(u, T)\sigma_d(u)
         + \left( - \rho_{f,FX} B_f(u, T)\sigma_f(u)
         + \rho_{d,FX} B_d(u, T)\sigma_d(u) \right) \sigma_{FX}(u) \right)\,\mathrm{d}u

        :param float s:
        :param float t:
        :return float:
        """
        if not self._foreign_correlation and not self._rate_correlation:
            return super(HullWhiteMultiCurrencyCurve, self).calc_integral_I2(s, t)

        terminal_date_yf = BusinessDate.diff_in_years(self.origin, self.terminal_date)

        func1 = (lambda u:
                 self.calc_integral_I1(u, t) * (self.volatility(u) ** 2 * self.calc_integral_B(u, t) -
                                                self._rate_correlation * self.volatility(u) *
                                                self._domestic_model.volatility(
                                                    u) * self._domestic_model.calc_integral_B(u, terminal_date_yf) -
                                                self._foreign_correlation * self.volatility(t) * self._fx_volatility(
                                                    t)))
        part1, err1 = integrate.quad(func1, s, t)

        part2 = self.calc_integral_B(s, t) * \
                self.calc_integral_I1(s, t) * \
                self.calc_integral_volatility_squared_with_I1_squared(0., s)

        return part1 + part2


class HullWhiteFxCurve(GBMFxCurve):
    @classmethod
    def cast(cls, fx_curve, domestic_curve, foreign_curve, volatility=0.0, correlation=None):
        r"""
        :param fx_curve: FxCurve to retrieve factor expectation
        :type  fx_curve: GBMFxCurve or FxCurve
        :param HullWhiteCurve domestic_curve: domestic HullWhiteCurve
        :param HullWhiteCurve foreign_curve: foreign HullWhiteCurve
        :param volatility: fx spot forward volatility
        :type  volatility: float or function
        :param correlation: correlation matrix indexed by risk factors
        :type  correlation: dict(RiskFactorModel, RiskFactorModel)

        Build HullWhiteFxCurve from HullWhiteCurves and GBMFxCurve.
        Terminal measure date in foreign_curve is ignored since it is taken from domestic_curve.

        """

        dx = correlation[domestic_curve, fx_curve] if correlation else 0.0
        fx = correlation[foreign_curve, fx_curve] if correlation else 0.0
        df = correlation[domestic_curve, foreign_curve] if correlation else 0.0

        new = cls(domestic_curve=domestic_curve, foreign_curve=foreign_curve, volatility=volatility,
                  domestic_correlation=dx, foreign_correlation=fx, rate_correlation=df,
                  inner_factor=fx_curve)
        return new

    def __init__(self, x_list=None, y_list=None, y_inter=None, origin=None, day_count=None,
                 domestic_curve=None, foreign_curve=None, volatility=0.0,
                 domestic_correlation=0., foreign_correlation=0., rate_correlation=0.,
                 inner_factor=None):
        """
        :param list(BusinessDate) x_list:
        :param list(BusinessDate) y_list:
        :param list() y_inter:
        :param BusinessDate origin:
        :param DayCount day_count:
        :param HullWhiteCurve domestic_curve:
        :param HullWhiteCurve foreign_curve:
        :param volatility:
        :type  volatility: float or function or Curve
        :param float domestic_correlation:
        :param float foreign_correlation:
        :param float rate_correlation:
        :param inner_factor:
        :type  inner_factor: GBMFxCurve or FxCurve
        """
        if inner_factor is None:
            inner_factor = FxCurve(x_list, y_list, y_inter, origin, day_count, domestic_curve, foreign_curve)
        else:
            if any([x_list, y_list, y_inter, origin, day_count]):
                raise (TypeError, 'If `inner_factor` is given all other `FxCurve` properties must be `None`.')
            if isinstance(inner_factor, GBMFxCurve):
                volatility = inner_factor.volatility

        # super(HullWhiteFxCurve, self).__init__(inner_factor.domain, [inner_factor(x) for x in inner_factor.domain],
        #                                        (inner_factor._y_left, inner_factor._y_mid, inner_factor._y_right),
        #                                        inner_factor.origin, inner_factor.day_count,
        #                                        domestic_curve, foreign_curve, volatility)
        super(HullWhiteFxCurve, self).__init__(inner_factor=inner_factor, volatility=volatility)

        assert self.origin == domestic_curve.origin == foreign_curve.origin
        self._df = inner_factor.get_fx_rate(domestic_curve.terminal_date) / \
                   inner_factor.get_fx_rate(self.origin)

        if isinstance(volatility, float):
            self.volatility = (lambda x: volatility)
        elif hasattr(volatility, 'to_curve'):
            self.volatility = volatility.to_curve()
        else:
            self.volatility = volatility

        self.domestic_curve = domestic_curve
        self.foreign_curve = foreign_curve

        self.foreign_correlation = foreign_correlation
        self.domestic_correlation = domestic_correlation
        self.rate_correlation = rate_correlation

        self._pre_calc_diffusion = dict()
        self._pre_calc_drift = dict()

        if isinstance(self.inner_factor, RiskFactorModel):
            self._diffusion_driver = self.domestic_curve, self.inner_factor, self.foreign_curve
        else:
            self._diffusion_driver = self.domestic_curve, self, self.foreign_curve

    # integrate drift and diffusion integrals

    def _calc_drift_integrals(self, s, e):
        start = BusinessDate.diff_in_years(self.origin, s)
        end = BusinessDate.diff_in_years(self.origin, e)

        func = (lambda u:
                self.foreign_curve.volatility(u) ** 2 +
                self.volatility(u) ** 2 +
                self.domestic_curve.volatility(u) ** 2 -
                self.rate_correlation * self.domestic_curve.volatility(u) * self.foreign_curve.volatility(u) +
                self.foreign_correlation * self.volatility(u) * self.foreign_curve.volatility(u) -
                self.domestic_correlation * self.volatility(u) * self.domestic_curve.volatility(u))
        part, err = integrate.quad(func, start, end)
        return -0.5 * part

    def _calc_diffusion_integrals(self, s, e):
        start = BusinessDate.diff_in_years(self.origin, s)
        end = BusinessDate.diff_in_years(self.origin, e)

        func = (lambda u: -self.domestic_curve.calc_integral_B(u, end) * self.domestic_curve.volatility(u))
        part_d, err = integrate.quad(func, start, end)

        func = (lambda u: -self.foreign_curve.calc_integral_B(u, end) * self.foreign_curve.volatility(u))
        part_f, err = integrate.quad(func, start, end)

        part_x, err = integrate.quad(self.volatility, start, end)
        return part_d, part_x, part_f

    # pre calculate integrals

    def pre_calculate(self, s, e):
        self._pre_calc_drift[s, e] = self._calc_drift_integrals(s, e)
        self._pre_calc_diffusion[s, e] = self._calc_diffusion_integrals(s, e)

    # evolve process

    def evolve(self, x, s, e, q):
        r"""
        :param float x: current state value, i.e. value before evolution step
        :param BusinessDate s: current point in time, i.e. start point of next evolution step
        :param BusinessDate e: next point in time, i.e. end point of evolution step
        :param float q: standard normal random number to do step
        :return float: next state value, i.e. value after evolution step

        evolves process state `x` from `s` to `e` in time depending of standard normal random variable `q`
        """
        d = self._calc_drift_integrals(s, e) if (s, e) not in self._pre_calc_drift else self._pre_calc_drift[s, e]
        v_d, v_x, v_f = self._calc_diffusion_integrals(s, e) \
            if (s, e) not in self._pre_calc_diffusion else self._pre_calc_diffusion[s, e]
        return x * exp(d - v_d * q[0] + v_x * q[1] + v_f * q[2])

    # FxCurve methods

    def get_fx_rate(self, value_date):
        y = self._factor_value * \
            self.foreign_curve.get_discount_factor(self._factor_date, value_date) / \
            self.domestic_curve.get_discount_factor(self._factor_date, value_date)
        return y
