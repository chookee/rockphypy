#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   AVO.py
@Time    :   2023/02/12 16:36:09
@Author  :   Jiaxin Yu 
@Contact :   yujiaxin666@outlook.com
@License :   (C)Copyright 2020-2021, Jiaxin Yu
'''

import numpy as np

def AVO_HTI(D1,D2,C1,C2,theta,azimuth):

    """Compute azimuth dependent PP reflectivity for wealy anisotropic HTI media using Ruger's approximation

    Args:
        D1 (g/cm3): density of the upper medium 
        D2 (g/cm3): density of the lower medium 
        C1 (matrix): stiffness matrix of the upper medium 
        C2 (matrix): stiffness matrix of the lower medium 
        theta (num or array like):  incident angle, in degree unit
        azimuth (num or array like): azimuth angle, in degree unit 

    Returns:
        Rpp: PP reflectivities
    """    
    theta = np.radians(theta)
    azimuth = np.radians(azimuth)
    C11_1=C1[0,0]
    C13_1=C1[0,2]
    C33_1=C1[2,2]
    C44_1=C1[3,3]
    C55_1=C1[4,4]
    C66_1=C1[5,5]

    C11_2=C2[0,0]
    C13_2=C2[0,2]
    C33_2=C2[2,2]
    C44_2=C2[3,3]
    C55_2=C2[4,4]
    C66_2=C2[5,5]

    alpha_1= np.sqrt(C33_1/D1)
    beta_1=np.sqrt(C44_1/D1)
    beta_v_1=np.sqrt(C55_1/D1)
    gamma_1= (C44_1-C66_1)/(2*C66_1)
    gamma_v_1= (C66_1-C44_1)/(2*C44_1)
    epsilon_v_1= (C11_1-C33_1)/(2*C33_1)
    delta_v_1= ((C13_1+C55_1)**2-(C33_1-C55_1)**2)/(2*C33_1*(C33_1-C55_1))
    
    Z_1=D1*alpha_1
    mu_1=D1*beta_1**2
    mu_v_1=D1*beta_v_1**2

    alpha_2= np.sqrt(C33_2/D2)
    beta_2=np.sqrt(C44_2 /D2 )
    beta_v_2=np.sqrt(C55_2 /D2 )
    gamma_2= (C44_2 -C66_2 )/(2*C66_2)
    gamma_v_2= (C66_2 -C44_2)/(2*C44_2)
    epsilon_v_2= (C11_2 -C33_2 )/(2*C33_2 )
    delta_v_2= ((C13_2 +C55_2 )**2-(C33_2-C55_2 )**2)/(2*C33_2 *(C33_2 -C55_2 ))
    
    Z_2=D2*alpha_2 
    mu_2=D2*beta_2**2
    mu_v_2=D2*beta_v_2**2

    dZ=Z_2-Z_1
    Z_=(Z_1+Z_2)/2
    dalpha=alpha_2-alpha_1
    alpha_=(alpha_1+alpha_2)/2
    beta_=(beta_1+beta_2)/2
    dmu=mu_2-mu_1
    mu_=(mu_1+mu_2)/2
    ddelta=delta_v_2-delta_v_1
    dgamma=gamma_2-gamma_1
    depsilon=epsilon_v_2-epsilon_v_1

    # full azimuth Rüger (1996)
    Rpp= 0.5*dZ/Z_+0.5*( dalpha/alpha_-(2*beta_/alpha_)**2* dmu/mu_+ (ddelta+2*(2*beta_/alpha_)**2 *dgamma)*np.cos(azimuth)**2)*np.sin(theta)**2 + 0.5*(dalpha/alpha_+depsilon* np.cos(azimuth)**4+ddelta*np.sin(azimuth)**2*np.cos(azimuth)**2)*np.sin(theta)**2*np.tan(theta)**2
    return Rpp

def Aki_Richard(theta, vp1,vp2,vs1,vs2,den1,den2):
    """Aki-Richard approximation to PP reflectivity. 

    Args:
        theta (degree): incident angle
        vp1 (m/s): P wave velocity of layer 1
        vp2 (m/s): P wave velocity of layer 2
        vs1 (m/s): S wave velocity of layer 1
        vs2 (m/s): S wave velocity of layer 2
        den1 (kg/m3): density of layer 1
        den2 (kg/m3): density of layer 2

    Returns:
        R_pp: P wave reflectivity
        R_ps: PS reflectivity
        Rpp0: intercept
        gradient
    Written by Jiaxin Yu
    """   
    theta=np.deg2rad(theta) # convert angle in degree to angle in radian
    delta_den=den2-den1
    delta_vp=vp2-vp1
    delta_vs=vs2-vs1
    rho_mean=0.5*(den1+den2)
    vp_mean=0.5*(vp1+vp2)
    vs_mean=0.5*(vs1+vs2)
    
    Rpp0=0.5*(delta_den/rho_mean+delta_vp/vp_mean)# intercept
    M= -2*(vs_mean/vp_mean)**2*(2*delta_vs/vs_mean+delta_den/rho_mean)
    N= 0.5* delta_vp/vp_mean
    R_pp= Rpp0+ M *np.sin(theta)**2 + N * np.tan(theta)**2
    gradient= M+N
    p=np.sin(theta)/vp1 # ray parameter

    cos_theta_s=np.sqrt(1-(np.sin(theta)**2.*(vs1**2/vp1**2)))

    R_ps=-0.5*p*vp_mean/cos_theta_s*((1-2*vs_mean**2*p**2+2*vs_mean**2*np.cos(theta)/vp_mean*cos_theta_s/vs_mean)*delta_den/rho_mean-(4*p**2*vs_mean**2-4*vs_mean**2*np.cos(theta)/vp_mean*cos_theta_s/vs_mean)*delta_vs/vs_mean)
    return R_pp,R_ps, Rpp0, gradient

def zoeppritz(vp1, vs1, rho1, vp2, vs2, rho2, theta):
    """Reflection & Transmission coefficients calculated using full Zoeppritz
    equations.

    Args:
    theta, vp1,vp2,vs1,vs2,den1,den2
        theta (degree): incident angle
        vp1 (m/s): P wave velocity of layer 1
        vp2 (m/s): P wave velocity of layer 2
        vs1 (m/s): S wave velocity of layer 1
        vs2 (m/s): S wave velocity of layer 2
        den1 (kg/m3): density of layer 1
        den2 (kg/m3): density of layer 2


    Returns:
        Rpp,Rps: PP and PS reflectivity
    """    
    theta1 = np.deg2rad(theta)
    p = np.sin(theta)/vp1 # Ray parameter
    # Transmission angle of P-wave
    theta2  =np.arcsin(p*vp2)
    phi1   = np.arcsin(p*vs1)# Reflection angle of converted S-wave
    phi2   = np.arcsin(p*vs2)# Transmission angle of converted S-wave
    
    a=rho2*(1-2*np.sin(phi2)**2)-rho1*(1-2*np.sin(phi1)**2)
    b=rho2*(1-2*np.sin(phi2)**2)+2*rho1*np.sin(phi1)**2
    c=rho1*(1-2*np.sin(phi1)**2)+2*rho2*np.sin(phi2)**2
    d=2*(rho2*vs2**2-rho1*vs1**2)
    H=a-d*np.cos(theta2)/vp2*np.cos(phi2)/vs2
    E=b*np.cos(theta1)/vp1+c*np.cos(theta2)/vp2
    F=b*np.cos(phi1)/vs1+c*np.cos(phi2)/vs2
    G=a-d*np.cos(theta1)/vp1*np.cos(phi2)/vs2
    D=E*F+G*H*p**2
    Rpp=( (  b*np.cos(theta1)/vp1-c*np.cos(theta2)/vp2)*F-( a+d*np.cos(theta1)/vp1*np.cos(phi2)/vs2)*H*p**2)/D

    Rps= (-2*np.cos(theta1)/vp1*(a*b+c*d*np.cos(theta2)/vp2*np.cos(phi2)/vs2)*p*vp1)/(vs1*D)

    # M = np.array([ 
    #     [-np.sin(theta1), -np.cos(phi1), np.sin(theta2), np.cos(phi2)],
    #     [np.cos(theta1), -np.sin(phi1), np.cos(theta2), -np.sin(phi2)],
    #     [2*rho1*vs1*np.sin(phi1)*np.cos(theta1), rho1*vs1*(1-2*np.sin(phi1)**2),
    #         2*rho2*vs2*np.sin(phi2)*np.cos(theta2), rho2*vs2*(1-2*np.sin(phi2)**2)],
    #     [-rho1*vp1*(1-2*np.sin(phi1)**2), rho1*vs1*np.sin(2*phi1), 
    #         rho2*vp2*(1-2*np.sin(phi2)**2), -rho2*vs2*np.sin(2*phi2)]
    #     ])
    
    # N = np.array([ 
    #     [np.sin(theta1), np.cos(phi1), -np.sin(theta2), -np.cos(phi2)],
    #     [np.cos(theta1), -np.sin(phi1), np.cos(theta2), -np.sin(phi2)],
    #     [2*rho1*vs1*np.sin(phi1)*np.cos(theta1), rho1*vs1*(1-2*np.sin(phi1)**2),
    #         2*rho2*vs2*np.sin(phi2)*np.cos(theta2), rho2*vs2*(1-2*np.sin(phi2)**2)],
    #     [rho1*vp1*(1-2*np.sin(phi1)**2), -rho1*vs1*np.sin(2*phi1),
    #         -rho2*vp2*(1-2*np.sin(phi2)**2), rho2*vs2*np.sin(2*phi2)]
    #     ])
    return Rpp, Rps

def AVO_abe(vp1,vs1,d1,vp2,vs2,d2):
	""" Copied from RPT matlab tools func: avo_abe
	Calculates AVO parameters:
		A: Intercept (P-P) i.e. normal incidence reflectivity
		B1, B2: P-P Gradient using different approximations
		E1, E2: P-S Gradient using different approximations
		B1 Shuey's paper (2terms->B Castag)
		B2 Castagna's paper->Shuey
		(note: both are Shuey's approximation, but B2 is using Castagna's "way" to calculate them. The results are slightly different)
		E1 Ezequiel Gonzalez approximation
		E2 Alejandro & Reinaldo approx

	Args:
		vp1 (m/s): P wave velocity of layer 1
		vs1 (m/s): S wave velocity of layer 1
		d1 (kg/m3): density of layer 1
		vp2 (m/s):P wave velocity of layer 2
		vs2 (m/s): S wave velocity of layer 2
		d2 (kg/m3): density of layer 2
	"""	

	da=(d1+d2)/2     
	Dd=(d2-d1)
	vpa=(vp1+vp2)/2  
	Dvp=(vp2-vp1)
	vsa=(vs1+vs2)/2  
	Dvs=(vs2-vs1)
	Ro=0.5*((Dvp/vpa)+(Dd/da))
	A=Ro

	# case 1 Shuey's paper (2terms->B Castag)
	poi1=((0.5*(vp1/vs1)**2)-1)/((vp1/vs1)**2-1)
	poi2=((0.5*(vp2/vs2)**2)-1)/((vp2/vs2)**2-1)
	poia=(poi1+poi2)/2   
	Dpoi=(poi2-poi1)
	Bx=(Dvp/vpa)/((Dvp/vpa)+(Dd/da))
	Ax=Bx-(2*(1+Bx)*(1-2*poia)/(1-poia))
	B1=(Ax*Ro)+(Dpoi/(1-poia)**2)
	# case 2 Castagna's paper->Shuey
	B2=(-2*vsa**2*Dd/(vpa**2*da)) + (0.5*Dvp/vpa)-(4*vsa*Dvs/(vpa**2))

	# E1 Gonzalez approx.
	E1=(-0.5*Dd/da)-((vsa/vpa)*((Dd/da)+(2*Dvs/vsa))) + (((vsa/vpa)**3)*((0.5*Dd/da)+(Dvs/vsa)))

	# E2 Alejandro & Reinaldo
	E2=-2*(vs1/vp1)*((Dd/da*(0.5+(0.25*vpa/vsa)))+ (Dvs/vsa))

	return A,B1,B2,E1,E2

def EI_ref(Vp,Vs,rho,theta,SP,norm=True):
    """Compute elastic impedance of an isotropic, flat-layered Earth 

    Args:
        Vp (scalar/array): _description_
        Vs (scalar/array): _description_
        rho (scalar/array): _description_
        theta (_type_): incident angle 
        SP (cons.): constant ratio of Vs to Vp, can be taken as the average of input Vs/Vp, i.e. SP= VS.mean()/VP.mean()
        norm (bool, optional): True: normalized input velocities and density such that the units and dimension match with acoustic impedance. Defaults to True.

    Returns:
        EI_pp: elastic impedance for PP reflection 
        EI_svp: elastic impedance for P-SV reflection 
        EI_psv: elastic impedance for SV-P reflection 
        EI_svsv: elastic impedance for SV-SV reflection 
        EI_shsh: elastic impedance for SH-SH reflection 
    
    """    
    
    theta = np.deg2rad(theta)
    p=np.sin(theta)
    theta_s = np.arcsin(p*Vs)
    ipn=1 
    isn=1 
    # normalize
    if norm==True:
        ipn= np.mean(Vp)*np.mean(rho)
        isn= np.mean(Vs)*np.mean(rho)
        Vp=Vp/np.mean(Vp)
        Vs=Vs/np.mean(Vs)
        rho=rho/np.mean(rho)
       
    # PP
    A = 1+np.tan(theta)**2
    B = -8*SP**2*np.sin(theta)**2
    C = 1-4*SP**2*np.sin(theta)**2
    EI_pp= ipn*Vp**A*Vs**B*rho**C
    # P SV
    B = np.sin(theta)/np.sqrt(1-SP**2*np.sin(theta)**2)*(4*np.sin(theta)**2*SP**2-4*SP*np.cos(theta)*np.sqrt(1-SP**2*np.sin(theta)**2))
    C = -np.sin(theta)/np.sqrt(1-SP**2*np.sin(theta)**2)*(1-2*np.sin(theta)**2*SP**2+2*SP*np.cos(theta)*np.sqrt(1-SP**2*np.sin(theta)**2))
    EI_psv= ipn*Vs**B*rho**C
    # SV P
    B = np.sin(theta_s)/np.sqrt(1-1/SP**2*np.sin(theta_s)**2)*(4*np.sin(theta_s)**2-4*SP*np.cos(theta_s)*np.sqrt(1-1/SP**2*np.sin(theta_s)**2))
    C = -np.sin(theta_s)/np.sqrt(1-1/SP**2*np.sin(theta_s)**2)*(1-2*np.sin(theta_s)**2+2*SP*np.cos(theta_s)*np.sqrt(1-1/SP**2*np.sin(theta_s)**2))
    EI_svp= isn*Vs**B*rho**C
    # SV-SV
    B = -1/np.cos(theta_s)**2+8*np.sin(theta_s)**2
    C = -1+4*np.sin(theta_s)**2
    EI_svsv= isn*Vs**B*rho**C
    # SH-SH
    B = -1+np.tan(theta_s)**2
    C = -1
    EI_shsh= isn*Vs**B*rho**C
    return EI_pp,EI_psv,EI_svp,EI_svsv,EI_shsh

def AVO_ortho(a1,b1,e11,d11,e12,d12,g1,rho1,a2,b2,e21,d21,e22,d22,g2,rho2,the):
    """calculates the reflectivity in the symmetry plane for interfaces between 2 orthorhombic media  

    Args:
        a1 (_type_): _description_
        b1 (_type_): _description_
        e11 (_type_): _description_
        d11 (_type_): _description_
        e12 (_type_): _description_
        d12 (_type_): _description_
        g1 (_type_): _description_
        rho1 (_type_): _description_
        a2 (_type_): _description_
        b2 (_type_): _description_
        e21 (_type_): _description_
        d21 (_type_): _description_
        e22 (_type_): _description_
        d22 (_type_): _description_
        g2 (_type_): _description_
        rho2 (_type_): _description_
        the (_type_): _description_

    Returns:
        _type_: _description_
    """    

    Z1=rho1*a1
    Z2=rho2*a2
    G1=rho1*b1*b1
    G2=rho2*b2*b2
    G=(G1+G2)/2
    dG=G2-G1

    a=(a1+a2)/2
    da=a2-a1
    b=(b1+b2)/2
    db=b2-b1

    the=the*np.pi/180

    sthe2=np.sin(the)**2
    tthe2=np.tan(the)**2

    f=(2*b/a)**2
    Rxz=(Z2-Z1)/(Z2+Z1)+0.5*(da/a-f*(dG/G-2*(g2-g1))+d22-d12)*sthe2+.5*(da/a+e22-e12)*sthe2*tthe2  
    Ryz=(Z2-Z1)/(Z2+Z1)+0.5*(da/a-f*dG/G+d21-d11)*sthe2+.5*(da/a+e21-e11)*sthe2*tthe2  

    return Rxz, Ryz