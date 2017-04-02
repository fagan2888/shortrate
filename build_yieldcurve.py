'''Code for generating a graph showing the effect of the different factors in
Nelson Siegel
'''

import matplotlib.pyplot as plt
import decimalpy as dp
import finance as fn

ns = fn.yieldcurves.NelsonSiegel(1, 1, 1, 1)
tau_list = dp.Vector([1, 4])
legend_list = [r"$\beta_0-factor$ is the same for both $\tau$'s"]
xdata = dp.Vector(range(61)) * 0.5
b0_factor = dp.Vector(61, 1)

plt.plot(xdata, b0_factor)
for tau in tau_list:
    ns.scale = 1 / tau
    plt.plot(
        xdata, ns.Slope(xdata),
        xdata, ns.Curvature(xdata)
    )
    for fac in (1,2):
        legend_list.append(r'$\beta_%s-factor, \tau = %s$' % (fac, tau))

tau_in_title = ' and '.join([r'$\tau = %s$' % x for x in tau_list])
plt.title(r'Showing Nelson Siegel curves for %s' % tau_in_title)
plt.xlabel('time (years)')
plt.grid(True)
plt.ylim(-0.5,1.5)
plt.legend(legend_list)
plt.show()


print list(ns.Curvature(xdata))