# -*- coding: utf-8 -*-

#  shortrate
#  -----------
#  risk factor model library python style.
#
#  Author:  sonntagsgesicht <sonntagsgesicht@github.com>
#  Website: https://github.com/sonntagsgesicht/shortrate
#  License: MIT (see LICENSE file)


from math import sqrt, exp

from businessdate import BusinessDate
from dcf import ZeroRateCurve, TIME_SHIFT, compounding
from scipy import integrate

from risk_factor_model import RiskFactorModel


class HullWhiteCurve(ZeroRateCurve, RiskFactorModel):
    """
    calculation of discount factors in the Hull White model
    """

    @classmethod
    def cast(cls, other, mean_reversion=0.0, volatility=0.0, terminal_date=None):
        """

        :param ZeroRateCurve other:
        :param mean_reversion: mean reversion speed of short rate process
        :type  mean_reversion: float or function
        :param volatility: short rate volatility
        :type  volatility: float or function
        :param BusinessDate terminal_date: date of terminal measure
        :return: HullWhiteCurve

        build HullWhiteCurve i.e. Hull White model in terminal measure from
        ZeroRateCurve, mean reversion speed, volatility and terminal measure date.
        """
        new = cls(mean_reversion=mean_reversion, volatility=volatility, terminal_date=terminal_date, inner_factor=other)
        return new

    def __init__(self, x_list=None, y_list=None, y_inter=None,
                 origin=None, day_count=None, forward_tenor=None,
                 mean_reversion=0.0, volatility=0.0, terminal_date=None, inner_factor=None):
        """
        :param list(float) x_list:
        :param list(float) y_list:
        :param list(interpolation) y_inter:
        :param BusinessDate origin:
        :param DayCount day_count:
        :param BusinessPeriod forward_tenor: standard forward
        :param mean_reversion: mean reversion speed of short rate process
        :type  mean_reversion: float or function
        :param volatility: short rate volatility
        :type  volatility: float or function
        :param BusinessDate terminal_date: date of terminal measure
        :param RateCurve inner_factor:

        initializes Hull White curve
        """

        if inner_factor is None:
            inner_factor = ZeroRateCurve(x_list, y_list, y_inter, origin, day_count, forward_tenor)
        else:
            if any([x_list, y_list, y_inter, origin, day_count, forward_tenor]):
                raise (TypeError, 'If `inner_factor` is given all other `RateCurve` properties must be `None`.')

        RiskFactorModel.__init__(self, inner_factor, 0.0)

        super(HullWhiteCurve, self).__init__(inner_factor.domain,
                                             [inner_factor.get_storage_type(x) for x in inner_factor.domain],
                                             (inner_factor._y_left, inner_factor._y_mid, inner_factor._y_right),
                                             inner_factor.origin, inner_factor.day_count,
                                             inner_factor.forward_tenor)

        # init mean reversion
        # time dependent mean reversion speed -> not implemented yet

        # if isinstance(mean_reversion, float):
        #     self.mean_reversion = (lambda x: mean_reversion)
        # elif hasattr(mean_reversion, 'origin'):
        #     self.mean_reversion = mean_reversion.to_curve()
        # else:
        #     self.mean_reversion = mean_reversion

        # init mean reversion
        if isinstance(mean_reversion, float):
            self.mean_reversion = mean_reversion
        else:
            raise NotImplementedError

        # init volatility
        if isinstance(volatility, float):
            self.volatility = (lambda x: volatility)
        elif hasattr(volatility, 'to_curve'):
            self.volatility = volatility.to_curve()
        else:
            self.volatility = volatility

        # terminal_date
        if terminal_date is None:
            terminal_date = self.domain[-1]
        self.terminal_date = terminal_date

        self._pre_calc_diffusion = dict()
        self._pre_calc_drift = dict()
        self._integral_vol_squared_I1 = dict()

        # factor state variables
        self._factor_date = self.origin
        self._factor_yf = 0.0
        self._factor_value = 0.0
        self._integral = 0.0

        if isinstance(self.inner_factor, RiskFactorModel):
            self._diffusion_driver = self.inner_factor
        else:
            self._diffusion_driver = self

    # integration helpers for Hull White model

    def calc_integral_I1(self, t1, t2):
        r"""
        :param float t1: start time as year fraction / float
        :param float t2: end time as year fraction / float
        :return: float


        returns the value of the helper function I1

        .. math::   I_1(t_1, t_2) = \exp
                    \left( -\int_{t_1}^{t_2} a(\tau) \,\mathrm{d}\tau \right) = \mathrm{e}^{-a(t_2 - t_1)}

        """
        return exp(-self.mean_reversion * (t2 - t1))

    def calc_integral_I1_squared(self, t1, t2):
        r"""
        :param float t1: start time as year fraction / float
        :param float t2: end time as year fraction / float
        :return float:

        returns the value of the helper function I1^2

        .. math::   I_1(t_1, t_2)^2 = \exp
                    \left( -2\int_{t_1}^{t_2} a(\tau) \,\mathrm{d}\tau \right) = \mathrm{e}^{-2a(t_2 - t_1)}

        """
        return exp(-2.0 * self.mean_reversion * (t2 - t1))

    def calc_integral_B(self, t1, t2):
        r"""
        returns the value of the helper function B

        .. math::   B(t_1, t_2) = \int_{t_1}^{t_2} I_1(t_1, \tau)  \,
                    \mathrm{d}\tau = \frac{1}{a}\Big(1 - \mathrm{e}^{-a(t_2 - t_1)}\Big)

        :param float t1: start time as year fraction / float
        :param float t2: end time as year fraction / float
        :return float:
        """

        return (1 - exp(- self.mean_reversion * (t2 - t1))) / self.mean_reversion

    def calc_integral_volatility_squared_with_I1(self, t1, t2):
        """
        :param t1:
        :param t2:
        :return float:

        Calculates integral of integrand :math:`f` with :math:`I_1`
        between two time points :math:`t_1` and :math:`t_2` with
        :math:`t_1 \le t_2` is as:

        .. math::   \textrm{Var}_r(t_1,t_2) =  \int_{t_1}^{t_2} vol(u)^2 I_1(u,t_2) \,\mathrm{d} u

        """

        func = (lambda x: self.volatility(x) ** 2 * self.calc_integral_I1(x, t2))
        result, err = integrate.quad(func, t1, t2)
        return result

    def calc_integral_volatility_squared_with_I1_squared(self, t1, t2):
        """
        :param t1:
        :param t2:
        :return float:

        calculates drift integral :math:`I_2`
        """
        func = (lambda x: self.volatility(x) ** 2 * self.calc_integral_I1_squared(x, t2))
        result, err = integrate.quad(func, t1, t2)
        return result

    def calc_integral_I2(self, s, t):
        """
        :param float s: start time as year fraction / float
        :param float t: end time as year fraction / float
        :return float:

        returns the value of the helper function Integrals

        One of the deterministic terms of a step in the MC simulation is calculated here
        with last observation date for T-Bond numeraire T

        .. math::   \int_s^t \sigma^2(u) I_1(u,t) (B(u,t)-B(u,T)) \,\mathrm{d} u +
                    B(s,t)I_1(s,t)\int_0^s \sigma^2(u) I_1^2(u,s)\,\mathrm{d}u

        """
        terminal_date_yf = BusinessDate.diff_in_years(self.origin, self.terminal_date)

        func1 = (lambda u:
                 self.volatility(u) ** 2 * self.calc_integral_I1(u, t) *
                 (self.calc_integral_B(u, t) -
                  self.calc_integral_B(u, terminal_date_yf)))
        part1and3, err1 = integrate.quad(func1, s, t)

        part2 = self.calc_integral_B(s, t) * \
                self.calc_integral_I1(s, t) * \
                self.calc_integral_volatility_squared_with_I1_squared(0., s)
        return part1and3 + part2

    # integrate drift integrals of curve part

    def _calc_integrals(self, e):
        """
        :param BusinessDate e: end date
        :return float:

        method to pre calculate :math:` \int_0^t \sigma(u)^2 I_1(u, t) du` along a grid

        """
        end = BusinessDate.diff_in_years(self.origin, e)
        return self.calc_integral_volatility_squared_with_I1(0.0, end)

    # integrate drift and diffusion integrals of stochastic process part

    def _calc_drift_integrals(self, s, e):
        """
        :param s:
        :param e:
        :return:

        method to pre calculate drift integrals along `s` to `e` on a grid

        """
        start = BusinessDate.diff_in_years(self.origin, s)
        end = BusinessDate.diff_in_years(self.origin, e)

        i1 = self.calc_integral_I1(start, end)
        i2 = self.calc_integral_I2(start, end)
        return i1, i2

    def _calc_diffusion_integrals(self, s, e):
        """
        :param s:
        :param e:
        :return:

        method to pre calculate diffusion integrals along `s` to `e` on a grid

        """
        start = BusinessDate.diff_in_years(self.origin, s)
        end = BusinessDate.diff_in_years(self.origin, e)

        var = self.calc_integral_volatility_squared_with_I1_squared(start, end)
        return sqrt(var)

    # RiskFactorModel methods

    def pre_calculate(self, s, e):
        """
        :param BusinessDate s: start date
        :param BusinessDate e: end date

        pre calculate values based only on grid points

        """
        self._integral_vol_squared_I1[e] = self._calc_integrals(e)
        self._pre_calc_drift[s, e] = self._calc_drift_integrals(s, e)
        self._pre_calc_diffusion[s, e] = self._calc_diffusion_integrals(s, e)

    def evolve(self, x, s, e, q):
        """
        :param x:
        :param s:
        :param e:
        :param q:
        :return:

        evolve Hull White process of shortrate diviation math:: y = r - y
        """
        i1, i2 = self._calc_drift_integrals(s, e) if (s, e) not in self._pre_calc_drift else self._pre_calc_drift[s, e]
        v = self._calc_diffusion_integrals(s, e) \
            if (s, e) not in self._pre_calc_diffusion else self._pre_calc_diffusion[s, e]
        return x * i1 + i2 + v * q

    def set_risk_factor(self, factor_date, factor_value=0.0):
        """
        :param BusinessDate factor_date: date of t
        :param float factor_value: value of risk factor y


        set :math:`y=r(t)-F(0,t)` risk factor and prepare discount factor integral
        .. :math:   ` \int_0^t \sigma(u)^2 I_1(u, t) du`

        """
        self._factor_date = factor_date
        self._factor_yf = BusinessDate.diff_in_years(self.origin, factor_date)
        self._factor_value = factor_value

        if factor_date in self._integral_vol_squared_I1:
            self._integral = self._integral_vol_squared_I1[factor_date]
        else:
            self._integral = self._calc_integrals(factor_date)
        return self

    # ZeroRateCurve methods

    def get_discount_factor(self, start_date, end_date):
        r"""

        :param BusinessDate start_date: start date
        :param BusinessDate end_date: end date
        :return float:

        calculate the discount rate for the given start date and end date

        ..  math::

            P_{u,y}: \textrm{BusinessDate} {\times} \textrm{BusinessDate} \to \mathbb{R}

        and

        ..  math::

            (s,t) \mapsto P_{\text{init}}(s,t) \exp \left(-\frac{1}{2}(B^2(u,t)-B^2(u,s))
            \int_0^u \sigma^2(\tau)I_1(\tau,t), \mathrm{d}\tau\right)\mathrm{e}^{-(B(t,T)-B(t,S))y}



        with :math:`P_{\text{init}}(s,t) = \verb|Curve.get_discount_curve(s,t)|`

        Here the variables with subscript :math:`\textrm{pld}` are dates (BusinessDate instances) and
        the variables without subscripts are year fractions between the correspondent
        :math:`\textrm{pld}` variables and :math:`\verb|validity_date|` in the default DCC (Act/365.25).

        """

        # assert self._factor_date <= S <= T

        df = self.inner_factor.get_discount_factor(start_date, end_date)

        loc_diff_in_years = BusinessDate.diff_in_years  # for speed opt use pointer

        factor_yf = self._factor_yf
        start_yf = loc_diff_in_years(self.origin, start_date)
        end_yf = loc_diff_in_years(self.origin, end_date)

        loc_calc_b = self.calc_integral_B  # for speed opt use pointer

        start_arg = loc_calc_b(factor_yf, start_yf)
        end_arg = loc_calc_b(factor_yf, end_yf)

        arg = (start_arg - end_arg) * (0.5 * (start_arg + end_arg) * self._integral + self._factor_value)

        return df * exp(arg)

    def get_zero_rate(self, S, T):
        """
        :param S:
        :param T:
        :return:

        calculate zero rate between `S` and `T`.
        """
        if S == T:
            T += TIME_SHIFT
            pass
        df = self.get_discount_factor(S, T)
        yf = self.day_count(S, T)
        return compounding.continuous_rate(df, yf)
