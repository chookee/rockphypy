#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''
@File    :   EM.py
@Time    :   2023/01/23 16:55:56
@Author  :   Jiaxin Yu 
@Contact :   yujiaxin666@outlook.com
@License :   (C)Copyright 2020-2021, Jiaxin Yu
'''


import numpy as np
from utils import *
from Anisotropy import *
from scipy.optimize import fsolve

def VRH(volumes,M):
    """Computes Voigt, Reuss, and Hill Average Moduli Estimate. 

    Args:
        volumes (array): volumetric fractions of N phases
        M (array): elastic modulus of the N phase.
    Returns:
        M_v: Voigt average
        M_r: Reuss average
        M_0: Hill average 
    Written by Jiaxin Yu (July 2021)
    """    
    M_v=np.dot(volumes,M)
    
    M_r=np.dot(volumes,1/M)**-1
    
    M_h= 0.5*(M_r+M_v)
    return  M_v,M_r,M_h

def cripor(K0, G0, phi, phic):
    """Critical porosity model according to Nur’s modified Voigt average. 
    
    Args:
        K0 (GPa): mineral bulk modulus 
        G0 (Gpa): mineral shear modulus 
        phi (frac): porosity
        phic (frac): critical porosity
    Returns:
        K_dry,G_dry (GPa): dry elastic moduli of the framework
    Refs: 
        Section 7.1 Rock physics handbook 2nd edition
    Written by Jiaxin Yu (July 2021)
    """    
    K_dry = K0 * (1-phi/phic)
    G_dry = G0 * (1-phi/phic)

    return K_dry, G_dry

def cripor_reuss(M0, Mf, phic, den=False):
    """In the suspension domain, the effective bulk and shear moduli of the rock can be estimated by using the Reuss (isostress) average. 

    Args:
        M0 (GPa/g.cc): The solid phase modulus or density
        Mf (GPa/g.cc): The pore filled phase modulus or density
        phic (frac): critical porosity
        den (bool, optional): If False: compute the reuss average for effective modulus of two mixing phases. If true, compute avearge density using mass balance, which corresponds to voigt average. Defaults to False.

    Returns:
        M (GPa/g.cc): average modulus or average density
    Refs: 
        Section 7.1 Rock physics handbook 2nd edition
    Written by Jiaxin Yu (July 2021)
    """   
    if den is False:

        M = VRH(np.array([M0,Mf]), np.array([(1-phic,phic)]))[1]
    else: 
        M = VRH(np.array([M0,Mf]), np.array([(1-phic,phic)]))[0]

    return M

def HS(f, K1, K2,G1, G2, bound='upper'): 
    """Compute effective moduli of two-phase composite using hashin-strikmann bounds. 

    Args:
        f (float): 0-1, volume fraction of stiff material  
        K1 (GPa): bulk modulus of stiff phase
        K2 (GPa): bulk modulus of soft phase
        G1 (GPa): shear modulus of stiff phase
        G2 (GPa): shear modulus of soft phase
        bound (str, optional): upper bound or lower bound. Defaults to 'upper'.
    Returns: 
        K, G (GPa): effective moduli of two-phase composite
    Written by Jiaxin Yu
    """    
    if bound == 'upper':  
        K=K1+ (1-f)/( (K2-K1)**-1 + f*(K1+4*G1/3)**-1 )

        Temp = (K1+2*G1)/(5*G1 *(K1+4*G1/3))
        G=G1+(1-f)/( (G2-G1)**-1 + 2*f*Temp)
    else:  
        K=K2+ f/( (K1-K2)**-1 + (1-f)*(K2+4*G2/3)**-1 )

        Temp = (K2+2*G2)/(5*G2 *(K2+4*G2/3))
        G=G2+f/( (G1-G2)**-1 + 2*(1-f)*Temp)
    return K, G

def Eshelby_Cheng(K, G, phi, alpha, Kf, mat=False):
    """ Compute the effective anisotropic moduli of a cracked isotropic rock with single set fracture using Eshelby–Cheng Model.

    Args:
        K (GPa): bulk modulus of the isotropic matrix
        G (GPa): shear modulus of the isotropic matrix
        phi (frac): (crack) porosity
        alpha (unitless): aspect ratio of crack
        Kf (GPa):  bulk modulus of the fluid. For dry cracks use fluid bulk modulus 0
        mat (bool, optional): If true: the output is in matrix form, otherwise  is numpy array. Defaults to False.

    Returns:
        C_eff: effective moduli of cracked, transversely isotropic rocks
    Refs:
        section 4.14 in The Rock Physics Handbook 
    Written by Jiaxin Yu 
    """    

    lamda = K-2*G/3 

    sigma = (3*K-2*G)/(6*K+2*G)
    R = (1-2*sigma)/(8*np.pi*(1-sigma))
    Q = 3*R/(1-2*sigma)
    Sa = np.sqrt(1-alpha**2)
    Ia = 2*np.pi*alpha*(np.arccos(alpha)-alpha*Sa)/Sa**3
    Ic = 4*np.pi-2*Ia
    Iac = (Ic-Ia)/(3*Sa**2)
    Iaa = np.pi-3*Iac/4
    Iab = Iaa/3

    S11 = Q*Iab+R*Ia
    S33 = Q*(4*np.pi/3 - 2*Iac*alpha**2)+Ic*R
    S12 = Q*Iab-R*Ia
    S13 = Q*Iac*alpha**2-R*Ia
    S31 = Q*Iac-R*Ic 
    S1212 = Q*Iab+R*Ia
    S1313 = Q*(1+alpha**2)*Iac/2 + R*(Ia+Ic)/2

    C = Kf/( 3*(K-Kf))
    D = S33*S11+S33*S12-2*S31*S13-(S11+S12+S33-1-3*C) - C*(S11+S12+2*(S33-S13-S31))
    E = S33*S11 - S31*S13 - (S33+S11-2*C-1) + C*(S31+S13-S11-S33)

    C11 = lamda*(S31-S33+1) + 2*G*E/ (D*(S12-S11+1))
    C33 = ((lamda+2*G)*(-S12-S11+1)+2*lamda*S13+4*G*C)/D
    C13 = ((lamda+2*G)*(S13+S31)-4*G*C+lamda*(S13-S12-S11-S33+2))/(2*D)
    C44 = G/(1-2*S1313)
    C66 = G/(1-2*S1212)

    if mat==False:
        C_eff = np.array([C11,C33,C13,C44,C66])
    else: 
        C_eff = write_VTI_matrix(C11,C33,C13,C44,C66)
    return C_eff

def Backus(V,lamda, G ):
    """Compute stiffnesses of a layered medium composed of thin isotropic layers using backus average model. 

    Args:
        V (num or array-like, frac): volumetric fractions of N isotropic layering materials
        lamda (num or array-like): Lamé coefficients of N isotropic layering materials
        G (num or array-like, GPa): shear moduli of N isotropic layering materials
    Returns:
        C11,C33,C13,C44,C66 (num or array-like, GPa): Elastic moduli of the anisotropic layered media

    Written by Jiaxin Yu
    """    
    C33=np.dot(V, 1/(lamda+2*G)) **-1
    C44=np.dot(V, 1/G)**-1
    C66=np.dot(V, G)
    C13=np.dot(V, 1/(lamda+2*G)) **-1 * np.dot(V, lamda/(lamda+2*G))
    C11=np.dot(V, 4*G*(lamda+G)/(lamda+2*G))+np.dot(V, 1/(lamda+2*G))**-1 * np.dot(V, lamda/(lamda+2*G))**2
    
    return C11,C33,C13,C44,C66



def hudson(K, G, Ki, Gi, alpha, crd, order=1, axis=3):
    """  Hudson’s effective crack model assuming weak inclusion for media with single crack set with all normals aligned along 1 or 3-axis. First and Second order corrections are both implemented. Notice that the second order correction has limitation. See Cheng (1993).         

    Args:
        K (GPa): bulk modulus of isotropic background
        G (GPa): shear modulus of isotropic background
        Ki (GPa): bulk modulus of the inclusion material. For dry cracks: Ki=0
        Gi (GPa): shear modulus of the inclusion material  
        alpha (unitless): crack aspect ratio
        crd (unitless): crack density 
        order (int, optional): approximation order. 
            1: Hudson's model with first order correction. 
            2: Hudson's model with first order correction.  
            Defaults to 1.
        axis (int, optional): axis of symmetry. 
            1: crack normals aligned along 1-axis, output HTI 
            3: crack normals aligned along 3-axis, output VTI 
            Defaults to 3

    Returns:
        C_eff: effective moduli in 6x6 matrix form. 
    """    

    lamda = K-2*G/3 
    kapa = (Ki+4*Gi/3)*(lamda+2*G)/(np.pi*alpha*G*(lamda+G))
    M = 4*Gi*(lamda+G)/(np.pi*alpha*G*(3*lamda+4*G))
    U1 = 16*(lamda+2*G)/(3*(3*lamda+4*G)*(1+M))
    U3 = 4*(lamda+2*G)/(3*(lamda+G)*(1+kapa))
    # first order corrections
    C11_1 = -lamda**2*crd*U3/G
    C13_1 = -lamda*(lamda+2*G)*crd*U3/G
    C33_1 = -(lamda+2*G)**2*crd*U3/G
    C44_1 = -G*crd*U1
    #C66_1 = 0
    # second order corrections
    q = 15*lamda**2/G**2+28*lamda/G + 28
    C11_2 = q/15 * lamda**2/(lamda+2*G) *(crd*U3)**2
    C13_2 = q/15 * lamda*(crd*U3)**2
    C33_2 = q/15 * (lamda+2*G)*(crd*U3)**2
    C44_2 = 2/15 * G*(3*lamda+8*G)/(lamda+2*G)*(crd*U1)**2
    #C66_2 = 0
    if order == 1:
        C11 = lamda+2*G+C11_1 
        C13 = lamda    +C13_1
        C33 = lamda+2*G+C33_1
        C44 = G        +C44_1
        C66 = G
    elif order == 2:
        C11 = lamda+2*G+C11_1+C11_2 
        C13 = lamda    +C13_1+C13_2
        C33 = lamda+2*G+C33_1+C33_2
        C44 = G        +C44_1+C44_2
        C66 = G
    
    if axis ==3: # VTI
        C_eff = write_VTI_matrix(C11,C33,C13,C44,C66)
    elif axis ==1: # HTI
        C_eff = write_HTI_matrix(C33,C11,C13,C66,C44)
    return C_eff
    
def hudson_rand(K, G, Ki, Gi, alpha, crd):
    """Hudson's crack model of a material containing randomly oriented inclusions. The model results agree with the self-consistent results of Budiansky and O’Connell (1976).

    Args:
        K (GPa): bulk modulus of isotropic background
        G (GPa): shear modulus of isotropic background
        Ki (GPa): bulk modulus of the inclusion material. For dry cracks: Ki=0
        Gi (GPa): shear modulus of the inclusion material, for fluid, Gi=0 
        alpha (unitless): crack aspect ratio
        crd (unitless): crack density

    Returns:
        K_eff, G_eff (GPa): effective moduli of the medium with randomly oriented inclusions 
    """    
    lamda = K-2*G/3 
    kapa = (Ki+4*Gi/3)*(lamda+2*G)/(np.pi*alpha*G*(lamda+G))
    M = 4*Gi*(lamda+G)/(np.pi*alpha*G*(3*lamda+4*G))
    U1 = 16*(lamda+2*G)/(3*(3*lamda+4*G)*(1+M))
    U3 = 4*(lamda+2*G)/(3*(lamda+G)*(1+kapa))
    # first order corrections
    G_1 = -2*G*crd*(3*U1+2*U3)
    lamda_1 = (1/3)*(-(3*lamda+2*G)**2*crd*U3/(3*G) - 2*G_1)
    lamda_eff = lamda+lamda_1
    G_eff = G+G_1
    K_eff = lamda_eff+2*G_eff/3 
    return K_eff,G_eff

def hudson_ortho(K, G, Ki, Gi, alpha, crd):
    """  Hudson’s first order effective crack model assuming weak inclusion for media with three crack sets with normals aligned along 1 2, and 3-axis respectively.  Model is valid for small crack density and aspect ratios.      

    Args:
        K (GPa): bulk modulus of isotropic background
        G (GPa): shear modulus of isotropic background
        Ki (GPa): bulk modulus of the inclusion material. For dry cracks: Ki=0
        Gi (GPa): shear modulus of the inclusion material  
        alpha (nd array with size 3): 
            [alpha1, alpha2,alpha3] aspect ratios of  three crack sets
        crd (nd array with size 3): 
            [crd1, crd2, crd3] crack densities of three crack sets 

    Returns:
        C_eff: effective moduli in 6x6 matrix form. 
    """    
    if type(alpha) == 'list' or type(crd) == 'list' :
        raise Exception("need python array as input for alpha and crd")

    lamda = K-2*G/3 
    kapa = (Ki+4*Gi/3)*(lamda+2*G)/(np.pi*alpha*G*(lamda+G))
    M = 4*Gi*(lamda+G)/(np.pi*alpha*G*(3*lamda+4*G))
    U1 = 16*(lamda+2*G)/(3*(3*lamda+4*G)*(1+M))
    U3 = 4*(lamda+2*G)/(3*(lamda+G)*(1+kapa))

    # first order corrections
    C11_1 = -lamda**2*crd*U3/G
    C13_1 = -lamda*(lamda+2*G)*crd*U3/G
    C33_1 = -(lamda+2*G)**2*crd*U3/G
    C44_1 = -G*crd*U1
    C12_1 = C11_1 # C12= C11-2C66
    #C66_1 = 0
    C11=lamda+2*G+C33_1[0]+C11_1[1]+C11_1[2]
    C12=lamda    +C13_1[0]+C13_1[1]+C12_1[2]
    C13=lamda    +C13_1[0]+C12_1[1]+C13_1[2]
    C22=lamda+2*G+C11_1[0]+C33_1[1]+C11_1[2]
    C23=lamda    +C12_1[0]+C13_1[1]+C13_1[2]
    C33=lamda+2*G+C11_1[0]+C11_1[1]+C33_1[2]
    C44=G        +C44_1[1]+C44_1[2]
    C55=G        +C44_1[0]+C44_1[2]
    C66=G        +C44_1[0]+C44_1[1]
    
    C_eff = write_matrix(C11,C22,C33,C12,C13,C23,C44,C55,C66)
    return C_eff

def hudson_cone(K, G, Ki, Gi, alpha, crd, theta):
    """  Hudson’s first order effective crack model assuming weak inclusion for media with crack normals randomly distributed at a fixed angle from the TI symmetry axis 3 forming a cone;     

    Args:
        K (GPa): bulk modulus of isotropic background
        G (GPa): shear modulus of isotropic background
        Ki (GPa): bulk modulus of the inclusion material. For dry cracks: Ki=0
        Gi (GPa): shear modulus of the inclusion material  
        alpha (unitless): aspect ratios of crack sets
        crd (unitless): total crack density 
        theta (degree): the fixed angle between the crack normam and the symmetry axis x3.
    Returns:
        C_eff: effective moduli of TI medium in 6x6 matrix form. 
    """    
    theta= np.deg2rad(theta) 
    lamda = K-2*G/3 
    kapa = (Ki+4*Gi/3)*(lamda+2*G)/(np.pi*alpha*G*(lamda+G))
    M = 4*Gi*(lamda+G)/(np.pi*alpha*G*(3*lamda+4*G))
    U1 = 16*(lamda+2*G)/(3*(3*lamda+4*G)*(1+M))
    U3 = 4*(lamda+2*G)/(3*(lamda+G)*(1+kapa))

    # first order corrections
    C11_1 = -crd/(2*G)*(U3*(2*lamda**2+4*lamda*G*np.sin(theta)**2+3*G**2*np.sin(theta)**4)+U1*G**2*np.sin(theta)**2*(4-3*np.sin(theta)**2))

    C33_1 = -crd/G*(U3*(lamda+2*G*np.cos(theta)**2)**2+U1*G**2*4*np.cos(theta)**2*np.sin(theta)**2)

    C12_1 = -crd/(2*G)*(U3*(2*lamda**2+4*lamda*G*np.sin(theta)**2+G**2*np.sin(theta)**4)-U1*G**2*np.sin(theta)**4)

    C13_1 = -crd/G*(U3*(lamda+G*np.sin(theta)**2)*(lamda+2*G*np.cos(theta)**2)-U1*G**2*2*np.sin(theta)**2*np.cos(theta)**2)

    C44_1 = -crd/2*G*(U3*4*np.sin(theta)**2*np.cos(theta)**2+U1*(np.sin(theta)**2+2*np.cos(theta)**2-4*np.sin(theta)**2*np.cos(theta)**2))

    C66_1 = -crd/2*G*(U3*4*np.sin(theta)**4+U1*np.sin(theta)**2*(2-np.sin(theta)**2))
    #C22_1 = C11_1
    #C23_1 = C13_1
    #C55_1 = C44_1
    C11=lamda+2*G+C11_1
    C12=lamda    +C12_1
    C13=lamda    +C13_1
    #C22=C11
    #C23=C13
    C33=lamda+2*G+C33_1
    C44=G        +C44_1
    #C55=C44     
    C66=G        +C66_1
    
    C_eff = write_matrix(C11,C11,C33,C12,C13,C13,C44,C44,C66)
    return C_eff

def Berrymann_sc(K,G,X,Alpha):
    """ Effective elastic moduli for multi-component composite using Berryman's Self-Consistent (Coherent Potential Approximation) method. 

    Args:
        K (array): 1d array of bulk moduli of N constituent phases, [K1,K2,...Kn]
        G (array): 1d array of shear moduli of N constituent phases, [G1,G2,...Gn]
        X (array): 1d array of volume fractions of N constituent phases, [x1,...xn], Sum(X) = 1.
        Alpha (array): aspect ratios of N constituent phases. Note that α <1 for oblate spheroids and α > 1 for prolate spheroids, α = 1 for spherical pores,[α1,α2...αn]
    See also: PQ_vectorize, Berrymann_func
    Returns:
        K_sc,G_sc: Effective bulk and shear moduli of the composite
    Written by Jiaxin Yu (July 2021)
    """    
   
    K_sc,G_sc=  fsolve(Berrymann_func, (K.mean(), G.mean()), args = (K,G,X,Alpha)) 
    return K_sc,G_sc

def PQ_vectorize(Km,Gm, Ki,Gi, alpha):    
    """ compute geometric strain concentration factors P and Q for prolate and oblate spheroids according to Berymann (1980). 
    
    Args:
        Km (GPa): Shear modulus of matrix phase. For Berrymann SC       approach, this corresponds to the effective moduli of the composite. 
        Gm (GPa): Bulk modulus of matrix phase. For Berrymann SC approach, this corresponds to the effective moduli of the composite.  
        Ki (array): 1d array of bulk moduli of N constituent phases, [K1,K2,...Kn]
        Gi (array): 1d array of shear moduli of N constituent phases, [G1,G2,...Gn]
        alpha (array): aspect ratios of N constituent phases. Note that α <1 for oblate spheroids and α > 1 for prolate spheroids, α = 1 for spherical pores,[α1,α2...αn]

    Returns:
        P,Q (array): geometric strain concentration factors, [P1,,,Pn],[Q1,,,Qn]
    See also: Berrymann_sc, Berrymann_func
    Written by Jiaxin Yu (July 2021)
    """
    dim = Ki.size
    P = np.empty(dim)
    Q = np.empty(dim)
    theta = np.empty(dim)
    alpha_ = alpha # copy and modfiy
    alpha_[alpha==1]=0.999 # when alpha_ is 1, the f is nan
    
    theta[alpha_<1]=alpha_[alpha_<1]/(1.0 - alpha_[alpha_<1]**2)**(3.0/2.0) * (np.arccos(alpha_[alpha_<1]) - alpha_[alpha_<1]*np.sqrt(1.0 - alpha_[alpha_<1]**2))

    theta[alpha_>1]=alpha_[alpha_>1]/(alpha_[alpha_>1]**2-1)**(3.0/2.0) * ( alpha_[alpha_>1]*(alpha_[alpha_>1]**2-1)**0.5 -np.cosh(alpha_[alpha_>1])**-1)

    f= alpha_**2*(3.0*theta - 2.0)/(1.0 - alpha_**2)
    A = Gi/Gm - 1.0
    B = (Ki/Km - Gi/Gm)/3.0
    R = Gm/(Km + (4.0/3.0)*Gm) # 
    F1 = 1.0 + A*(1.5*(f + theta) - R*(1.5*f + 2.5*theta - 4.0/3.0))
    F2 = 1.0 + A*(1.0 + 1.5*(f + theta) - R*(1.5*f + 2.5*theta)) + B*(3.0 - 4.0*R) + A*(A + 3.0*B)*(1.5 - 2.0*R)*(f + theta - R*(f - theta + 
    2.0*theta**2))
    F3 = 1.0 + A*(1.0 - f - 1.5*theta + R*(f + theta))
    F4 = 1.0 + (A/4.0)*(f + 3.0*theta - R*(f - theta))
    F5 = A*(-f + R*(f + theta - 4.0/3.0)) + B*theta*(3.0 - 4.0*R)
    F6 = 1.0 + A*(1.0 + f - R*(f + theta)) + B*(1.0 - theta)*(3.0 - 4.0*R)
    F7 = 2.0 + (A/4.0)*(3.0*f + 9.0*theta - R*(3.0*f + 5.0*theta)) + B*theta*(3.0 - 4.0*R)
    F8 = A*(1.0 - 2.0*R + (f/2.0)*(R - 1.0) + (theta/2.0)*(5.0*R - 3.0)) + B*(1.0 - theta)*(3.0 - 4.0*R)
    F9 = A*((R - 1.0)*f - R*theta) + B*theta*(3.0 - 4.0*R)
    Tiijj = 3*F1/F2
    Tijij = Tiijj/3 + 2/F3 + 1/F4 + (F4*F5 + F6*F7 - F8*F9)/(F2*F4)
    P = Tiijj/3
    Q = (Tijij - P)/5
    # find and replace P and Q with alpha==1
    P[alpha==1]=(Km+4*Gm/3)/(Ki[alpha==1]+4*Gm/3)
    kesai= Gm/6 *(9*Km+8*Gm)/(Km+2*Gm)
    Q[alpha==1]= (Gm+kesai)/(Gi[alpha==1]+kesai)
    return P, Q
def Berrymann_func(params, K,G,X,Alpha ): 
    """Form the system of equastions to solve. See 4.11.14 and 4.11.15 in Rock physics handbook 2020

    Args:
        params: Parameters to solve, K_sc, G_sc
        
        K (array): 1d array of bulk moduli of N constituent phases, [K1,K2,...Kn]
        G (array): 1d array of shear moduli of N constituent phases, [G1,G2,...Gn]
        X (array): 1d array of volume fractions of N constituent phases, [x1,...xn]
        Alpha (array): aspect ratios of N constituent phases. Note that α <1 for oblate spheroids and α > 1 for prolate spheroids, α = 1 for spherical pores,[α1,α2...αn]
    See also: Berrymann_sc
    Written by Jiaxin Yu (July 2021)
    Returns:
        Eqs to be solved
    """    
  
    K_sc, G_sc = params
    P, Q = PQ_vectorize(K_sc,G_sc, K,G, Alpha)
    eq1 = np.sum(X*(K-K_sc)*P)
    eq2 = np.sum(X*(G-G_sc)*Q)
    return  [eq1,eq2]


def OConnell_Budiansky(K0,G0,crd):
    """self-consistent approximation  effective bulk and shear moduli of a cracked medium with randomly oriented dry penny-shaped cracks,  aspect ratio goes to 0

    Args:
        K0 (GPa): bulk modulus of background medium
        G0 (GPa): shear modulus of background medium
        crd (unitless): crack density

    Returns:
        K_dry,G_dry: dry elastic moduli of cracked medium
    """    
    nu0 = (3*K0-2*G0)/(6*K0+2*G0)#  Poisson ratio of the uncracked solid

    nu_eff = nu0*(1-16*crd/9) # approximation of the effective poisson'ratio of cracked solid
    K_dry = K0*(1-16*(1-nu_eff**2)*crd/(9*(1-2*nu_eff)))
    G_dry = G0*(1-32*(1-nu_eff)*(5-nu_eff)*crd/(45*(2-nu_eff)))
    return K_dry,G_dry

def OConnell_Budiansky_fl(K0,G0,Kfl,crd, alpha):
    """ Saturated effective elastic moduli using the O’Connell and Budiansky Self Consistent (SC) formulations under the constraints of small aspect ratio cracks with soft-fluid saturation.

    Args:
        K0 (GPa): bulk modulus of background medium
        G0 (GPa): shear modulus of background medium
        Kfl (GPa): bulk modulus of soft fluid inclusion, e.g gas
        crd (unitless): crack density
        alpha (unitless): aspect ratio

    Returns:
        K_sat,G_sat: elastic moduli of cracked background fully saturated by soft fluid.

    Refs: 
        O’Connell and Budiansky, (1974)
    """    
    
    nu0 = (3*K0-2*G0)/(6*K0+2*G0)#  Poisson ratio of the uncracked solid
    w = Kfl/alpha/K0
    # given crack density and w, solve for the D and nu_eff simulaneously using equations 23 and 25 in O’Connell and Budiansky, (1974)
    nu_eff, D =  fsolve(OC_R_funcs, (0.2, 0.9), args = (crd,nu0,w))   

    K_sat = K0*(1-16*(1-nu_eff**2)*crd*D/(9*(1-2*nu_eff)))
    G_sat = G0*(1-32/45*(1-nu_eff) *(D+ 3/(2-nu_eff))*crd)
    return K_sat,G_sat

def OC_R_funcs(params, crd,nu_0,w ): # crd, nu_0,w 
    """Form the system of equastions to solve. Given crack density and w, solve for the D and nu_eff simulaneously using equations 23 and 25 in O’Connell and Budiansky, (1974)

    Args:
        params : Parameters to solve, in the form of [nu_eff, D]
        crd (unitless): crack density
        nu_0 (num): Poisson's ratio of background medium
        w (unitless): softness indicator of fluid filled crack, w=Kfl/alpha/K0, soft fluid saturation is w is the order of 1 

    Returns:
        eqs to be solved
    
    """    
    nu_eff, D = params
    
    eq1 = 45/16 * (nu_0-nu_eff)/(1-nu_eff**2)*(2-nu_eff)/(D*(1+3*nu_0)*(2-nu_eff)-2*(1-2*nu_0)) - crd   # eq 23 in OC&R, 1974
    eq2 = crd * D**2-( crd+9/16 * (1-2*nu_eff)/(1-nu_0**2) + 3*w/(4*np.pi))*D + 9/16 * (1-2*nu_eff)/(1-nu_0**2) # eq 23 in OC&R, 1974
    return  [eq1,eq2]



