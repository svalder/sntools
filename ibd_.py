from math import pi, sqrt


targets_per_molecule = 2 # number of free protons per water molecule
pid = -11


'''
Particle physics section.
* cross section for neutrino-electron scattering
* directionality of scattered electron

Based on Strumia/Vissani (2003), arXiv:astro-ph/0302055.
'''
mN = 939.5654 # neutron mass (MeV)
mP = 938.2721 # proton mass (MeV)
mE = 0.5109989 # electron mass (MeV)
mPi = 139.57018 # pion mass (MeV)
delta = mN-mP
mAvg=(mP+mN)/2
gF=1.16637e-11 # Fermi coupling constant

def t_eNu_eE(eNu, eE):
	return mN**2 - mP**2 - 2*mP*(eNu-eE)
def x(eNu, eE):
	return t_eNu_eE(eNu, eE) / (4*mAvg**2)
def y(eNu, eE):
	return 1 - t_eNu_eE(eNu, eE)/710000
def z(eNu, eE):
	return 1 - t_eNu_eE(eNu, eE)/1000000
def f1(eNu, eE):
	return (1 - 4.706*x(eNu, eE)) / ((1-x(eNu, eE)) * y(eNu, eE)**2)
def f2(eNu, eE):
	return 3.706 / ((1-x(eNu, eE)) * y(eNu, eE)**2)
def g1(eNu, eE):
	return -1.27 / z(eNu, eE)**2
def g2(eNu, eE):
	return 2 * g1(eNu, eE) * mAvg**2 / (mPi**2 - t_eNu_eE(eNu, eE)) 

# AM, BM and CM for approximate calculation of absMsquared,
# AM1, BM1 and CM1 for more precise calculation
def AM(eNu, eE):
	return (mAvg**2 * (f1(eNu, eE)**2 - g1(eNu, eE)**2) * (t_eNu_eE(eNu, eE)-mE**2)) - (mAvg**2 * delta**2 * (f1(eNu, eE)**2 + g1(eNu, eE)**2)) - (2 * mE**2 * mAvg * delta * g1(eNu, eE) *(f1(eNu, eE)+f2(eNu, eE)))
def AM1(eNu, eE):
	return  1./16 * ( 
	(t_eNu_eE(eNu, eE) - mE**2) * (
		4 * f1(eNu, eE)**2 * (4*mAvg**2 + t_eNu_eE(eNu, eE) + mE**2)
		+ 4 * g1(eNu, eE)**2 * (-4*mAvg**2 + t_eNu_eE(eNu, eE) + mE**2)
		+ f2(eNu, eE)**2 * ((t_eNu_eE(eNu, eE)**2)/(mAvg**2) + 4*t_eNu_eE(eNu, eE) + 4*mE**2)
		+ 4*mE**2 * t_eNu_eE(eNu, eE) * g2(eNu, eE)**2 / mAvg**2
		+ 8*f1(eNu, eE)*f2(eNu, eE) * (2*t_eNu_eE(eNu, eE) + mE**2)
		+ 16*mE**2 * g1(eNu, eE)*g2(eNu, eE))
	- delta**2 * (
		(4*f1(eNu, eE)**2 + t_eNu_eE(eNu, eE) * f2(eNu, eE)**2 / mAvg**2) *
		(4*mAvg**2 + t_eNu_eE(eNu, eE) - mE**2)
		+ 4*g1(eNu, eE)**2 * (4*mAvg**2 - t_eNu_eE(eNu, eE) + mE**2)
		+ 4*mE**2 * g2(eNu, eE)**2 * (t_eNu_eE(eNu, eE) - mE**2) / mAvg**2
		+ 8*f1(eNu, eE)*f2(eNu, eE) * (2*t_eNu_eE(eNu, eE) - mE**2)
		+ 16*mE**2 * g1(eNu, eE)*g2(eNu, eE))
	- 32*mE**2 * mAvg * delta * g1(eNu, eE)*(f1(eNu, eE) + f2(eNu, eE)))

def BM(eNu, eE):
	return t_eNu_eE(eNu, eE)*g1(eNu, eE)*(f1(eNu, eE)+f2(eNu, eE))
def BM1(eNu, eE):
	return 1./16 * (
	16*t_eNu_eE(eNu, eE) * g1(eNu, eE)*(f1(eNu, eE) + f2(eNu, eE))
	+ 4*mE**2 * delta * (f2(eNu, eE)**2 + f1(eNu, eE)*f2(eNu, eE) + 2*g1(eNu, eE)*g2(eNu, eE))/mAvg)

def CM(eNu, eE):
	return ((f1(eNu, eE)**2) + (g1(eNu, eE)**2))/4
def CM1(eNu, eE):
	return 1./16 * (4*(f1(eNu, eE)**2 + g1(eNu, eE)**2) - t_eNu_eE(eNu, eE) * f2(eNu, eE)**2 / mAvg**2)

def sMinusU(eNu, eE):
	return 2*mP*(eNu+eE) - mE**2

def absMsquared(eNu, eE):
	return AM(eNu, eE) - sMinusU(eNu, eE) * BM(eNu, eE) + sMinusU(eNu, eE)**2 * CM(eNu, eE)

def dSigmadE(eNu, eE):
	return 2 * mP * gF**2 * 0.9746**2 / (8 * pi * mP**2 * eNu**2) * absMsquared(eNu, eE)



# probability distribution for the angle at which the positron is emitted
# numerical values are from Ishino-san's code for SK, based on email from Vissani
def dir_nuebar_p_sv(eNu, cosT):
	c1 = -0.05396 + 0.35824 * (eNu/100) + 0.03309 * (eNu/100)**2
	c2 =  0.00050 - 0.02390 * (eNu/100) + 0.14537 * (eNu/100)**2
	return 0.5 + c1 * cosT + c2 * (cosT**2 -1./3)


def get_eE(eNu, cosT):
	epsilon = eNu/mP
	kappa = (1 + epsilon)**2 - (epsilon * cosT)**2
	return ((eNu - delta_cm) * (1 + epsilon) + epsilon * cosT * sqrt((eNu - delta_cm)**2 - mE**2 * kappa)) / kappa


# calculate range for eE from eNu in center-of-mass (cm) frame
def s(eNu):
	return 2*mP*eNu + mP**2
def pE_cm(eNu):
	return (sqrt((s(eNu)-(mN-mE)**2)*(s(eNu)-(mN+mE)**2)))/(2*sqrt(s(eNu)))
def eE_cm(eNu):
	return (s(eNu)-mN**2+mE**2)/(2*sqrt(s(eNu)))

# Bounds for integration over eE
delta_cm = (mN**2 - mP**2 - mE**2) / (2*mP)
def eE_min(eNu):
	return eNu - delta_cm - (eNu/sqrt(s(eNu)) * (eE_cm(eNu) + pE_cm(eNu)))
def eE_max(eNu):
	return eNu - delta_cm - (eNu/sqrt(s(eNu)) *(eE_cm(eNu) - pE_cm(eNu)))
def bounds_eE(eNu, *args): # ignore additional arguments handed over by scipy.integrate.nquad()
	return [eE_min(eNu)+1, eE_max(eNu)+1]

# Bounds for integration over eNu
eThr = ((mN+mE)**2 - mP**2) / (2*mP) # threshold energy for IBD
bounds_eNu = [eThr, 100]
