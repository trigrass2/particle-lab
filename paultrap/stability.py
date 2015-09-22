import math

import numpy as np
import matplotlib.pyplot as plt
from uncertainties import ufloat, umath, unumpy as unp

from matplotlib.ticker import FuncFormatter, FixedLocator
from scipy.optimize import curve_fit, leastsq

from constants import *

def _double_sort(list1, list2):
	order = list1.argsort()
	return list1[order], list2[order]
	
def _ufloat_from_fitresult(popt, pcov):
	return tuple(ufloat(a, b) for a, b in zip(popt, np.sqrt(np.diag(pcov))))
	
def _uarray_fit(func, x, y, x0, B=100, **kwargs):

	def _derivative(func, x, *params, h=1e-6):
		return (-func(x+2*h, *params) + 8*func(x+h, *params) - 8*func(x-h, *params) + func(x-2*h, *params))/(12*h)
		
	def _chi(params, func, xn, yn, xs, ys):
		difference = yn - func(xn, *params)
		error = np.sqrt( np.power(_derivative(func, xn, *params) * xs, 2) + np.power(ys, 2) )
		chi = difference / error
		return chi
	
	means = []
	for i in range(B):
		indices = np.random.randint(0, len(x), size=len(x))
		popt, pcov, infodict, mesg, ier = leastsq(
			_chi, 
			x0=tuple(x0),
			args=(func, unp.nominal_values(x[indices]), unp.nominal_values(y[indices]), unp.std_devs(x[indices]), unp.std_devs(y[indices])),
			full_output=True, 
			**kwargs
		)
		if ier not in (1,2,3,4):
			raise ValueError("Optimal parameters not found. Message:", mesg)
		else:
			means.append(popt)
	
	popt, pcov = np.mean(means, axis=0), np.std(means, axis=0)
	results = tuple(ufloat(a, b) for a, b in zip(popt, pcov))
	
	#chisqndof = np.power(_chi(popt, func, unp.nominal_values(x), unp.nominal_values(y), unp.std_devs(x), unp.std_devs(y)), 2).sum() / (len(x)-len(x0))
	#print("Chi^2/ndof =", chisqndof)
	
	return results

def _normalize_ufloat(x):
	if math.isinf(x.s):
		x = ufloat(x.n, 0)
	if math.isinf(x.n):
		x = ufloat(0, x.s)
	return x
	
def _apply_additional_proportional_error(uarray, factor):
	return unp.uarray(unp.nominal_values(uarray), np.sqrt(np.power(unp.std_devs(uarray), 2) + np.power(factor*unp.nominal_values(uarray), 2)))

def stability(ux, ug_crit, omega, label=None):
	formatter = FuncFormatter(lambda x, pos: "%g\u00B2" % np.sqrt(x))
	locator = FixedLocator(np.power(unp.nominal_values(ux), 2), nbins=None)

	ux, ug_crit = _double_sort(ux, ug_crit)
	
	x = np.power(ux, 2)
	y = ug_crit
	
	line = plt.errorbar(unp.nominal_values(x), unp.nominal_values(y), xerr=unp.std_devs(x), yerr=unp.std_devs(y), fmt='o', label=label)
	color = line.lines[0].get_color()
	
	plt.gca().xaxis.set_major_formatter(formatter)
	plt.gca().xaxis.set_major_locator(locator)
	plt.xlabel(r"$U_x^2$")
	plt.ylabel(r"$U_g$")
	
	linear = lambda x, a: a*x
	a = _uarray_fit(linear, x, y, x0=(0.0001,), epsfcn=1e-7)[0]
	
	x = np.linspace(0, unp.nominal_values(x).max()*1.1, 20)
	y = linear(x, a.n)

	plt.plot(x, linear(x, a.n), color=color, label="Slope: {:P}".format(a))
	plt.fill_between(x, linear(x, a.n+a.s), linear(x, a.n-a.s), color=color, alpha=0.2)
	
	a = _normalize_ufloat(a)
	print("Slope:", a)
	
	qm = -2/3 * a * r0**2 * omega**2 / K
	
	print(label, "q/m =", qm*1e6, "uC/kg")
	
def day2_air():
	plt.clf()
	ux = unp.uarray([1000, 860, 800, 760, 1000, 920, 620], ux_error) # V
	ug_crit_1 = unp.uarray([390, 170, 600, 120, 225, 175, 53], ug_error) # V
	ug_crit_2 = unp.uarray([390, 170, 600, 120, 160, 145, 67], ug_error) # V
	ug_crit_3 = unp.uarray([390, 370, 600, 120, 225, 175, 67], ug_error) # V
	omega = 2*math.pi * ufloat(28,1) # Hz
	
	ux *= ux_correction
	for i, ug_crit in enumerate((ug_crit_1, ug_crit_2, ug_crit_3), 1):
		ug_crit = _apply_additional_proportional_error(ug_crit, stability_uncertainty_air)
		ug_crit *= ug_correction	
		
		stability(ux, ug_crit, omega, "Particle %d" % i)
	
	plt.title("Air 1")
	plt.legend(loc=2)
	plt.show()
	
	plt.clf()
	ux = unp.uarray([550, 740, 870, 1040], ux_error)
	ug_crit = unp.uarray([39, 84, 133, 147], ug_error)
	omega = 2*math.pi * ufloat(32,1) # Hz
	
	ug_crit = _apply_additional_proportional_error(ug_crit, stability_uncertainty_air)
	ux *= ux_correction
	ug_crit *= ug_correction
	
	stability(ux, ug_crit, omega, label="Particle 1")
	
	plt.title("Air 2")
	plt.legend(loc=2)
	plt.show()
	
def day3_vacuum():
	plt.clf()
	ux = unp.uarray([800, 1000, 500], ux_error) # V
	ug_crit = unp.uarray([110, 140, 30], ug_error) # V
	omega = 2*math.pi * ufloat(48,1) # Hz
	
	ug_crit = _apply_additional_proportional_error(ug_crit, stability_uncertainty_vacuum)
	ux *= ux_correction
	ug_crit *= ug_correction
	
	stability(ux, ug_crit, omega, label="Particle 1")
	
	plt.title("Vacuum 1 (300 mbar)")
	plt.legend(loc=2)
	plt.show()
	
	plt.clf()
	ux = unp.uarray([700, 800], ux_error) # V
	ug_crit = unp.uarray([100, 140], ug_error) # V
	omega = 2*math.pi * ufloat(45,1) # Hz
	
	ug_crit = _apply_additional_proportional_error(ug_crit, stability_uncertainty_vacuum)
	ux *= ux_correction
	ug_crit *= ug_correction
	
	stability(ux, ug_crit, omega, label="Particle 1")
	
	plt.title("Vacuum 2 (180 mbar)")
	plt.legend(loc=2)
	plt.show()
	
	
if __name__=="__main__":
	day2_air()
	day3_vacuum()