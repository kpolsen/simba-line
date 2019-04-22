"""

Regardless of RD's comment on caesar gas field, we are sticking with caesar gas mass so that gas_f_neu, f_h2 is consistent. Otherwise the number don't add up. Meaning that

gal.masses['HI'] >> np.sum(gas_f_neu * gas_m)
so then gas_f_neu wouldn't be useful anymore.

"""


from __future__ import print_function, division
from astropy import constants as constants
from readgadget import *
from astropy import units as u


def def_caesarFileName():
    infile = caesar_dir + name_prefix + '{:0>3}'.format(int(snap)) + \
        '.hdf5'
    return infile


def read_caesarCat(infile, redshiftDecimal=2, LoadHalo=False):
    obj = caesar.load(infile, LoadHalo=LoadHalo)
    redshift = np.round(obj.simulation.redshift, redshiftDecimal)
    h = obj.simulation.hubble_constant

    print(redshift)
    return obj, redshift, h


def load_cosmology(obj):
    """
    Parameters
    ----------
    obj: caesar obj

    Returns
    -------
    redshift: float

    rhomean: float
        mean baryon density in cgs

    """

    redshift = obj.simulation.redshift
    from astropy.cosmology import FlatLambdaCDM
    cosmo = FlatLambdaCDM(H0=100*obj.simulation.hubble_constant, Om0=obj.simulation.omega_matter, Ob0=obj.simulation.omega_baryon,Tcmb0=2.73)  # set our cosmological parameters
    thubble = cosmo.age(redshift).value  # age of universe at this redshift
    print('Read z=%g thubble=%g Gyr Ngal=%d'%(np.round(redshift,2),thubble,len(obj.galaxies)))
    print(cosmo)

    rhomean = obj.simulation.omega_matter*cosmo.critical_density(redshift).value
    return redshift, rhomean


def def_snapFileName(raw_sim_dir, raw_sim_name_prefix, snap):

    snapfile = raw_sim_dir + raw_sim_name_prefix + '{:0>3}'.format(int(snap)) + '.hdf5'
    return snapfile


def read_snapFile(snapfileName):
    import pygad as pg
    s = pg.Snap(snapfileName)
    h = s.cosmology.h()
    return s, h


def get_masses_all_galaxy(obj): # , snapFile):
    """

    get masses of each galaxy using CAESAR.

    This is not the particle mass.

    [u'H2', u'H', u'bh', u'gas', u'stellar', u'HI', u'baryon', u'dust', u'total']

    Parameters
    ----------
    obj: caesar obj

    Return
    ------
    gas_m: array
        incl. dust because dust is coupled to gas in simba

    dust_m: array
        dust only

    star_m: array

    dm_m: array
        TO be Implemented.. if needed...

    bh_m: array

    mHI: array

    mH2: array

    fHI: array

    fH2: array


    NOTE
    ----
    some galaxies will have 0 BH mass, but we haven't filter them out at this stage

    """
    # total_m = np.asarray([i.masses['total'] for i in obj.galaxies])  # not sure what mass this is ....

    _gas_m = np.asarray([i.masses['gas'] for i in obj.galaxies])
    dust_m = np.asarray([i.masses['dust'] for i in obj.galaxies])
    star_m = np.asarray([i.masses['stellar'] for i in obj.galaxies])
    bh_m = np.asarray([i.masses['bh'] for i in obj.galaxies])
    mHI = np.asarray([i.masses['HI'] for i in obj.galaxies])
    mH2 = np.asarray([i.masses['H2'] for i in obj.galaxies])
    gas_m = mHI + mH2

    print("gas field versus HI + H2 mass")
    print(_gas_m/gas_m)
    import pdb; pdb.set_trace()

    # uncomment below to get dm_m, but only if we figure out if there's a DMlist in CAESAR obj
    # if not 'dm' in obj.galaxies[0].masses.keys():
    #     dm_m = get_partmasses_from_snapshot(snapFile, obj, ptype='dm')
    #     dm_m = parse_particleMass_to_galMass(obj, dm_m, ptype='dm')

    #     from yt import YTQuantity
    #     for num, galaxy in enumerate(obj.galaxies):
    #         galaxy.masses['dm'] = YTQuantity(dm_m[num], "Msun")

    # return gas_m, dust_m, star_m, dm_m, bh_m, mHI, mH2, fHI, fH2

    return _gas_m, dust_m, star_m, bh_m, mHI, mH2, fHI, fH2, gas_m


def get_masses_each_galaxy(galaxy):
    """

    Using CAESAR to get the masses of each galaxy, note that we cannot get DM mass using this function. See get_masses_all_galaxy()

    Parameters
    ----------
    galaxy:
        caesar Galaxy object
        e.g., obj.galaxies[0]

    NOTE
    ----
    dust is coupled to gas, so a subset of gas mass is dust mass in simba (I believe..), so the definition of
         galaxy.masses['baryon'] = galaxy.masses['stellar'] + galaxy.masses['gas'] + galaxy.masses['bh']


    """
    print(galaxy.masses.keys())
    # [u'H2', u'H', u'bh', u'gas', u'stellar', u'HI', u'baryon', u'dust', u'total']

    # dark matter? Seems like we can only get that from the snapshot file -- not saved in CAESAR
    gas_m = galaxy.masses['gas']
    star_m = galaxy.masses['stellar']
    bh_m = galaxy.masses['bh']
    mHI = galaxy.masses['HI']
    mH2 = galaxy.masses['H2']

    return gas_m, star_m, bh_m, mHI, mH2


def get_partmasses_from_snapshot(snapFile, obj, ptype, physicalUnit=True, verbose=False):
    """

    Use readgadget to read in the info of each particles.

    Parameters
    ----------
    snapFile: str

    obj: caesar obj

    ptype: str
        'dm', 'star', 'gas', 'dust'

    physicalUnits: bool
        should be True in most cases

    Returns
    -------
    m: array
        array of mass for each particle

    NOTE
    ----
    Note "gas" mass is just the "cold gas" identified in the galaxy using the 6dFOF group finding which is restricted to cold gas > 0.13 atom/cc, does NOT include all the HI since self-shielding kicks in at ~1E-3 cc.

    RD: usually ignore 'gas' and just directly use 'HI' and 'H2' as total gas content.


    """

    if physicalUnit:
        units = 1
    else:
        units = 0

    h = obj.simulation.hubble_constant

    if ptype == 'dm':
        try:
            m = readsnap(snapFile,'mass','dm',units=units)/h
        except:
            return 0.0

    elif ptype == 'gas':
        m = readsnap(snapFile,'mass','gas',units=units)/h    # solar mass

    elif ptype == 'dust':
        m = readsnap(snapFile,'Dust_Masses','gas')*1.e10/h

    elif ptype == 'star':
        m = readsnap(snapFile,'mass','star',units=units,
                          suppress=1)/h  # suppress means no output print to command line
    if verbose:
        print("Number of {:} particles in snapshot file {:}: {:}").format(ptype, snapFile, len(m))

    return m



def parse_particleMass_to_galMass(obj, pmd, ptype):
    """
    Take an array of masses of each (dust or gas) particle found in the snapshot, return an array of masses, where element is the mass of one galaxy.

    Parameters
    ----------
    obj: caesar obj

    pmd: array
        of masses of all particles (of a given type) found in that snapshot
        only work if this is dust or gas or star particles

    ptype: str
        type of particles
        'star', 'gas', or 'dust'

    Return
    ------
    mass_array: numpy array
        mass of all galaxies identified in the CAESAR catalog

    """
    import numpy as np
    mass_array = []

    for g in obj.galaxies:
        if ptype == 'dust' or ptype == 'gas':
            md = np.array([pmd[k] for k in g.glist])
            mass_array.append(np.sum(md))
        elif ptype == 'star':
            md = np.array([pmd[k] for k in g.slist])
            mass_array.append(np.sum(md))
        else:
            raise NotImplementedError("Unclear particle types...")

    mass_array = np.asarray(mass_array)
    return mass_array



def parse_particleFraction_to_galFraction(obj, frac, weight):
    """
    Take an array of gas fraction for each gas particle found in the snapshot, return an array for each galaxy.

    Parameters
    ----------
    obj: caesar obj

    frac: array
        gas fraction of something for each particle

    weight: array
        use to weight
        probbaly use the masses of all gas particles found in that snapshot

    Return
    ------
    f_array: numpy array
        fraction of some type of gas for all galaxies identified in the CAESAR catalog

    """
    import numpy as np
    f_array = []

    for g in obj.galaxies:
        fracGal = np.array([frac[k] for k in g.glist])
        mm = np.array([weight[k] for k in g.glist])
        f_array.append(np.sum(mm * fracGal)/np.sum(mm))

    f_array = np.asarray(f_array)
    return f_array



def get_gas_misc_global(snapFile, obj, weight, physicalUnit=True):
    """

    get other gas-related variable fields, global properties


    Parameters
    ----------
    snapFile: str

    weight: array or float
        used to add the particles back together
        probably best choice is gas mass of each particle

    physicalUnit: bool


    Return
    ------

    """
    if physicalUnit:
        units = 1
    else:
        units = 0

    Mp = 1.67262189821e-24

    h = obj.simulation.hubble_constant
    redshift = obj.simulation.redshift

    #electron number density, relative to H density, n_H (should be between 0-1.17 or so)
    gas_x_e = readsnap(snapFile,'ne','gas',units=units)
    gas_x_e = parse_particleFraction_to_galFraction(obj, gas_x_e, weight=weight)

    gas_f_ion = gas_x_e / max(gas_x_e)
    gas_f_HI = 1 - gas_f_ion        # this includes atomic and molecuar gas for sure.

    # neutral hydrogen fraction (between 0-1)
    gfHI = readsnap(snapFile,'nh','gas',units=units)
    assert abs(gfHI.all()) <= 1.0      # each particles

    # each galaxy
    gfHI = parse_particleFraction_to_galFraction(obj, gfHI, weight=weight)
    gas_f_neu = gfHI        # only includes atomic gas but not molecular?


    # molecular gas fraction
    gfH2 = readsnap(snapFile,'fH2','gas', units=units)
    assert abs(gfH2.all()) <= 1.0      # each particles

    #each galaxy
    gas_f_H2 = parse_particleFraction_to_galFraction(obj, gfH2, weight=weight)


    # SFR
    gas_SFR = np.asarray([i.sfr for i in obj.galaxies])   # instantaneous SFR of galaxy, according to which we used to sort galaxy; see parse_simba.select_SFgal_from_simba()

    # Temperature in K
    gas_Tk = readsnap(snapFile,'u','gas',units=units)
    gas_Tk = parse_particleFraction_to_galFraction(obj, gas_Tk, weight=weight)

    # Smoothing length
    gas_h = readsnap(snapFile,'hsml','gas',units=units)/h/(1+redshift)  # smoothing length in ckpc --> proper kpc
    gas_h = parse_particleFraction_to_galFraction(obj, gas_h, weight=weight)

    # # gas-phase Z --> see get_Z_from_caesar()
    # gmet = readsnap(snapFile,'metals','gas',units=units)
    # Zname_0,ZSolar0, gas_Z = LoadMetal(gmet,0)      # slower
    # psfr = readsnap(snapFile,'sfr','gas',units=units,suppress=1)/h
    # gas_Z = parse_particleFraction_to_galFraction(obj, gas_Z, weight=psfr)

    # Stellar Z
    # pmetarray = readsnap(snapFile,'Metallicity','star',units=1,suppress=1)
    # star_m = get_partmasses_from_snapshot(snapFile, obj, ptype='star')
    # star_Z = parse_particleFraction_to_galFraction(obj, pmetarray, weight=star_m)

    return gas_f_HI, gas_f_neu, gas_f_H2, gas_SFR, gas_Tk, gas_h


def fraction_gas_phase_per_galaxy(gas_density, gas_m, gas_Tk):
    """

    Rough fraction of different gas phases of a galaxy.
    see reference from e.g., https://en.wikipedia.org/wiki/Interstellar_medium

    but note, by "cold" we mean 1e5 because this is cosmological scale.

    Parameters
    ----------
    gas_density: array
        gas density [1/cc]

    gas_m: array
        gas mass of all galaxies found in this snapshot

    gas_Tk: array


    Return
    ------
    fdiff: float
        cold, diffuse

    fcond: float
        cold, dense

    fwhim: float
        warm, dense

    fhot: float
        hot, diffuse


    """
    fdiff = np.round(sum(gas_m[(gas_density<100)&(gas_Tk<1e5)])/sum(gas_m),4)
    # e.g., WNM

    fcond = np.round(sum(gas_m[(gas_density>100)&(gas_Tk<1e5)])/sum(gas_m),6)  # e.g., molecular and CNM

    fwhim = np.round(sum(gas_m[(gas_density<100)&(gas_Tk>1e5)])/sum(gas_m),4)
    # e.g., warm, hot ionized medium

    fhot = np.round(sum(gas_m[(gas_density>100)&(gas_Tk>1e5)])/sum(gas_m),6)
    # .e.g, HII region

    return fdiff, fcond, fwhim, fhot


def group_part_by_galaxy(snapPart, galaxy, ptype):
    """
        take an array of particles and then return an array containing only the particles that belong to the given galaxy.
    """

    if ptype == 'gas':
        snapPart = np.array([snapPart[k] for k in galaxy.glist])
    elif ptype == 'star':
        snapPart = np.array([snapPart[k] for k in galaxy.slist])
    else:
        raise NotImplemented("Unclear ptype")
    return snapPart

def get_Z_from_caesar(obj):
    """

    Get global gas-phase and stellar Z of galaxies in the CAESAR catalog.

    NOTE
    ----
    gas-phase Z is weighted by SFR because it is closer to what is done observationally.  Think about how gas-phase metallicities are observed, via nebular emission lines.  The strength of these emission lines is approximately proportional to the SFR.  Hence SFR weighting is a fairer comparison to data than mass-weighting.

    For stellar metallicities, mass-weighting is somewhat more appropriate, though not strictly so since stellar absorption features are often dominated (in light) from giant stars.

    """
    factor = 0.0134      # Zsolar
    gas_Z = np.asarray([i.metallicities['sfr_weighted'] for i in obj.galaxies])/factor     # Normalized by Zsolar
    star_Z = np.asarray([i.metallicities['stellar'] for i in obj.galaxies])/factor

    return gas_Z, star_Z


def LoadMetal(gmet, MetIndex):
    """

    Get metallicity of given element, normalized by solar abundance

    Parameters
    ----------
    gmet: CAESAR Z

    MetIndex: int
        0 = H, 1 = He, 2 = C, 3 = N, etc; see note below

    Return
    ------
    MetName[MetIndex]: str
        Name of the species

    SolarAbundances[MetIndex]: float
        Solar abundance for the given species

    Zmet: float
        Metallicity of the required element, normalized by Z


    NOTE
    ----
        FYI: Gizmo metallicity structure
        All.SolarAbundances[0]=0.0134;        // all metals (by mass); present photospheric abundances from Asplund et al. 2009 (Z=0.0134, proto-solar=0.0142) in notes;
        All.SolarAbundances[1]=0.2485;    // He  (10.93 in units where log[H]=12, so photospheric mass fraction -> Y=0.2485 [Hydrogen X=0.7381]; Anders+Grevesse Y=0.2485, X=0.7314)
        All.SolarAbundances[2]=2.38e-3; // C   (8.43 -> 2.38e-3, AG=3.18e-3)
        All.SolarAbundances[3]=0.70e-3; // N   (7.83 -> 0.70e-3, AG=1.15e-3)
        All.SolarAbundances[4]=5.79e-3; // O   (8.69 -> 5.79e-3, AG=9.97e-3)
        All.SolarAbundances[5]=1.26e-3; // Ne  (7.93 -> 1.26e-3, AG=1.72e-3)
        All.SolarAbundances[6]=7.14e-4; // Mg  (7.60 -> 7.14e-4, AG=6.75e-4)
        All.SolarAbundances[7]=6.71e-3; // Si  (7.51 -> 6.71e-4, AG=7.30e-4)
        All.SolarAbundances[8]=3.12e-4; // S   (7.12 -> 3.12e-4, AG=3.80e-4)
        All.SolarAbundances[9]=0.65e-4; // Ca  (6.34 -> 0.65e-4, AG=0.67e-4)
        All.SolarAbundances[10]=1.31e-3; // Fe (7.50 -> 1.31e-3, AG=1.92e-3)

    """
    MetName = ['H','He','C','N','O','Ne','Mg','Si','S','Ca','Fe']
    SolarAbundances=[0.0134, 0.2485, 2.38e-3, 0.70e-3, 5.79e-3, 1.26e-3, 7.14e-4, 6.17e-4, 3.12e-4, 0.65e-4, 1.31e-3]
    Zmet = np.asarray([i[MetIndex] for i in gmet])
    Zmet /= SolarAbundances[MetIndex]
    return MetName[MetIndex],SolarAbundances[MetIndex],Zmet


def check_dense_gas(dir='./'):
    """

    Check the number of gas particles in each galaxy that has non-zero H2 fraction. This will determine how many GMCs we will get in the subgrid step in galaxy.add_GMCs(). If this number is low, then we might as well skip extracting that galaxy.

    """
    import glob
    import pandas as pd
    ff = glob.glob('*.gas')

    for i in ff:
        f = pd.read_pickle(i)
        print(i)
        print (f['f_H21'] > 0.0).sum()

        print("Total dense gas mass: ")
        print(f['m'] * f['f_H21']).sum()
    return None


if __name__ == '__main__':

    import _pickle as pickle
    try:
        from parse import *
    except:
        from parse_simba import *
    import socket
    import os
    import sys
    import numpy as np
    import caesar
    import matplotlib.pyplot as plt


    debug = False
    verbose = True
    caesarRotate = False

    snapRange = [36]    # don't put 036
    zCloudy = 6
    raw_sim_name_prefix = 'snap_m25n1024_'
    name_prefix = 'm25n1024_'
    min_dense_gas = 1.e4       # Msun

    host = socket.gethostname()
    if 'ursa' in host:
        raw_sim_dir = '/disk01/rad/sim/m25n1024/s50/'
        caesar_dir = '/disk01/rad/sim/m25n1024/s50/Groups/'
        redshiftFile = '/home/rad/gizmo-extra/outputs_boxspace50.info'
        d_data = '/home/dleung/Downloads/SIGAME_dev/sigame/temp/z' + str(int(zCloudy)) + '_data_files/'
    elif 'flatironinstitute.org' or 'worker' in host:
        raw_sim_dir = '/mnt/ceph/users/daisyleung/simba/sim/m25n1024/s50/'  # dummy
        caesar_dir = '/mnt/ceph/users/daisyleung/simba/sim/m25n1024/s50/Groups/'
        redshiftFile = '/mnt/ceph/users/daisyleung/simba/gizmo-extra/outputs_boxspace50.info'
        d_data = '/mnt/home/daisyleung/Downloads/SIGAME_dev/sigame/temp/z' + str(int(zCloudy)) + '_data_files/'

    snap = snapRange[0]
    infile = caesar_dir + name_prefix + '{:0>3}'.format(int(snap)) + \
        '.hdf5'
    print("Loading Ceasar file: {:}".format(infile))
    obj = caesar.load(infile, LoadHalo=False)

    h = obj.simulation.hubble_constant
    redshift = obj.simulation.redshift

    Mp = 1.67262189821e-24
    kpc2m = 3.085677580666e19

    # snap
    snapFile = def_snapFileName(raw_sim_dir, raw_sim_name_prefix, snap)

    # load in the fields from snapshot
    print("Read in gas fields")

    # from YT
    import pandas as pd
    sim_gas = pd.read_pickle('/mnt/home/daisyleung/Downloads/SIGAME_dev/sigame/temp/z6_data_files/particle_data/sim_data/z5.93_h0_s36_G0_sim.gas')
    sim_star = pd.read_pickle('/mnt/home/daisyleung/Downloads/SIGAME_dev/sigame/temp/z6_data_files/particle_data/sim_data/z5.93_h0_s36_G0_sim.star')

    redshift, rhomean = load_cosmology(obj)

    rho_crit_cgs = 1.8791e-29      # /h^2
    unit_Density = rho_crit_cgs *h*h * u.g/(u.cm**3)
    gas_densities_p = readsnap(snapFile,'rho','gas',units=1)
                      # gas density in comoving g/cm^3
    # print("density g/cc")
    # print(gas_densities_p.min(), gas_densities_p.max())
    #

    if verbose or debug:
        # not acutally used in the dataframe
        gas_nh_p = gas_densities_p*h*h*0.76/Mp     # number density of H in 1/cc

    gas_p_m = get_partmasses_from_snapshot(snapFile, obj, ptype='gas')
    gas_Tk_p = readsnap(snapFile,'u','gas',units=1)
    gas_SFR_p = readsnap(snapFile,'sfr','gas',units=1,suppress=1)/h
    gmet_p = readsnap(snapFile,'metals','gas',units=1)
    # Smoothing length
    gas_h_p = readsnap(snapFile,'hsml','gas',units=1)/h/(1+redshift)  # smoothing length in ckpc --> proper kpc
    #
    gas_pos_p = readsnap(snapFile,'pos','gas',units=1,suppress=1)/h # ckpc
    gas_vel_p = readsnap(snapFile,'vel','gas',units=1,suppress=1)   # km/s

    # molecular gas fraction
    gfH2_p = readsnap(snapFile,'fH2','gas', units=1)
    assert abs(gfH2_p.all()) <= 1.0      # each particles
    # neutral hydrogen fraction (between 0-1)
    gfHI_p = readsnap(snapFile,'nh','gas',units=1)
    assert abs(gfHI_p.all()) <= 1.0      # each particles

    gas_x_e_p = readsnap(snapFile,'ne','gas',units=1)

    if debug:
        nH = gfHI_p*gas_densities_p/Mp              # number density
        print('nH: ')
        print('from gfHI and gas density of readsnap')
        print(nH.max(), nH.min())
        print("from gas density of readsnap and 0.76: ")
        print(gas_nh_p.max(), gas_nh_p.min())
        plt.figure()
        plt.hist(nH, bins=100)
        plt.hist(gas_nh_p, bins=100)
        plt.show(block=False)
        plt.savefig('123.pdf')
        nE = gas_x_e_p * nH
       # nE = [a*b for a,b in zip(gas_x_e_p, nH)]
        print("Electron Number Density: ")
        print(nE)
        import pdb; pdb.set_trace()

    print("Read in stellar fields")
    star_p_m = get_partmasses_from_snapshot(snapFile, obj, ptype='star')
    star_pos_p =readsnap(snapFile,'pos','star',units=1,suppress=1)/h   # ckpc
    star_vel_p =readsnap(snapFile,'vel','star',units=1,suppress=1)
    pmetarray = readsnap(snapFile,'Metallicity','star',units=1,suppress=1)[:, 0]
    sage = readsnap(snapFile,'age','star',units=1,suppress=1)    #  expansion factor of formation

    print("Read in DM mass for each particle: " )
    dm_p_m = get_partmasses_from_snapshot(snapFile, obj, ptype='dm')

    savepath = 'xxx/' # d_data + 'particle_data/sim_data/'
    if not os.path.exists(savepath):
        os.makedirs(savepath)

    obj.galaxies.sort(key=lambda x: x.sfr, reverse=True)
    SolarAbundances=[0.0134, 0.2485, 2.38e-3, 0.70e-3, 5.79e-3, 1.26e-3,
                     7.14e-4, 6.17e-4, 3.12e-4, 0.65e-4, 1.31e-3]
    galName = []
    for gg, gal in enumerate(obj.galaxies):

        loc = gal.pos    # ckpc

        galname = 'h' + str(int(gal.parent_halo_index)) + '_s' + \
            str(int(snap)) + '_G' + str(int(gg))
        if verbose:
            print(galname)
            print("SFR: {:.2f}".format(gal.sfr))

        gas_m = group_part_by_galaxy(gas_p_m, gal, ptype='gas')
        gas_densities = group_part_by_galaxy(gas_densities_p, gal, ptype='gas')

        if debug:
            print("from readsnap: ")
            print(gas_densities.max(), gas_densities.min())    # g/cc
            print("from YT sphere: ")
            print(sim_gas['nH'].max(), sim_gas['nH'].min())
            gas_nh = group_part_by_galaxy(gas_nh_p, gal, ptype='gas')
            print(gas_nh.max(), gas_nh.min())      # 1/cc
            import pdb; pdb.set_trace()

        gas_Tk = group_part_by_galaxy(gas_Tk_p, gal, ptype='gas')
        gas_SFR = group_part_by_galaxy(gas_SFR_p, gal, ptype='gas')
        gas_Z = group_part_by_galaxy(gmet_p[:, 0], gal, ptype='gas')/SolarAbundances[0]
        gas_Z_1 = group_part_by_galaxy(gmet_p[:, 1], gal, ptype='gas')/SolarAbundances[1]
        gas_Z_2 = group_part_by_galaxy(gmet_p[:, 2], gal, ptype='gas')/SolarAbundances[2]
        gas_Z_3 = group_part_by_galaxy(gmet_p[:, 3], gal, ptype='gas')/SolarAbundances[3]
        gas_Z_4 = group_part_by_galaxy(gmet_p[:, 4], gal, ptype='gas')/SolarAbundances[4]
        gas_Z_5 = group_part_by_galaxy(gmet_p[:, 5], gal, ptype='gas')/SolarAbundances[5]
        gas_Z_6 = group_part_by_galaxy(gmet_p[:, 6], gal, ptype='gas')/SolarAbundances[6]
        gas_Z_7 = group_part_by_galaxy(gmet_p[:, 7], gal, ptype='gas')/SolarAbundances[7]
        gas_Z_8 = group_part_by_galaxy(gmet_p[:, 8], gal, ptype='gas')/SolarAbundances[8]
        gas_Z_9 = group_part_by_galaxy(gmet_p[:, 9], gal, ptype='gas')/SolarAbundances[9]
        gas_Z_10 = group_part_by_galaxy(gmet_p[:, 10], gal, ptype='gas')/SolarAbundances[10]

        # smoothing length
        gas_h = group_part_by_galaxy(gas_h_p, gal, ptype='gas')

        gas_pos = group_part_by_galaxy(gas_pos_p, gal, ptype='gas') # /obj.simulation.boxsize

        if len(gal.slist) < 64 or len(gal.glist) < 64:
            print("Too few star particles or gas particles, unlikely to be real galaxy or useful for our purpose. Skipping ", galname)
            continue

        gas_pos -= loc.d          # both are in comoving
        gas_pos /= (1+redshift)   # physical kpc
        gas_vel = group_part_by_galaxy(gas_vel_p, gal, ptype='gas')

        if caesarRotate:
            gas_pos = caesar.utils.rotator(gas_pos, gal.rotation_angles['ALPHA'].astype('float64'), gal.rotation_angles['BETA'].astype('float64'))
            gas_vel = caesar.utils.rotator(gas_vel,
                                          np.float64(gal.rotation_angles['ALPHA']),
                                          np.float64(gal.rotation_angles['BETA']))
            ff = lambda x: x.d
            gas_x = ff(gas_pos[:, 0])
            gas_y = ff(gas_pos[:, 1])
            gas_z = ff(gas_pos[:, 2])

            gas_vx = ff(gas_vel[:,0])
            gas_vy = ff(gas_vel[:,1])
            gas_vz = ff(gas_vel[:,2])
        else:
            gas_x = gas_pos[:, 0]
            gas_y = gas_pos[:, 1]
            gas_z = gas_pos[:, 2]

            gas_vx = gas_vel[:,0]
            gas_vy = gas_vel[:,1]
            gas_vz = gas_vel[:,2]

        gas_f_H2 = group_part_by_galaxy(gfH2_p, gal, ptype='gas')
        gas_f_neu = group_part_by_galaxy(gfHI_p, gal, ptype='gas')   # f_neu

        if debug:
            print("HI fraction")
            print(gas_f_neu.min(), gas_f_neu.max())    # following RD's def.
            print((1-gas_f_H2).min(), (1-gas_f_H2).max())
            print((gas_f_neu/(1-gas_f_H2)).min())
            print((gas_f_neu/(1-gas_f_H2)).max())

        # neutral gas from 1- ionized gas
        gas_x_e = group_part_by_galaxy(gas_x_e_p, gal, ptype='gas')   # relative to nH
        gas_f_ion = gas_x_e / max(gas_x_e)
        gas_f_HI = 1 - gas_f_ion
        assert abs(gas_f_HI.all()) <= 1.0

        if debug:
            print(gas_f_HI >= gas_f_neu)     # former incl. also molecular
            print((gas_f_HI >= gas_f_neu).all())   # expecting True
            import pdb; pdb.set_trace()

        if debug:
            print('\nChecking molecular gas mass fraction from simulation:')
            print('%.3s %% \n' % (np.sum(gas_m * gas_f_H2) / np.sum(gas_m) * 100.))
            #
            print("gas mass from snapshot: {:.2f} [x1e8 Msun]".format(gas_m.sum()/1.e8))
            print("gas mass from 'gas' from caesar {:.2f} [x1e8 Msun]".format(gal.masses['gas']/1.e8))
            #
            print('gas mass from (HI + H2) from caesar {:.2f} [x1e8 Msun]'.format((gal.masses['HI'] + gal.masses['H2'])/1.e8))
            print('')
            print("gas fraction from caesar: {:.2f}".format(gal.gas_fraction))
            print('gas fraction from Mgas/(Mgas+Mstar): {:.2f} '.format(gal.masses['gas']/(gal.masses['gas'] + gal.masses['stellar'])))
            print('gas fraction from MHI + MH2 /(MHI + MH2 + Mstar): {:.2f}'.format((gal.masses['HI'] + gal.masses['H2']) / (gal.masses['HI'] + gal.masses['H2'] + gal.masses['stellar'])))
            #
            print(gal.masses['HI'], np.sum(gas_f_neu * gas_m))
            import pdb; pdb.set_trace()

        # apply some selection criteria:
        # 1) SFR > 0.1 Msun/yr
        # 2) dense gas mass > 1.e5 Msun; otherwise we will get an error in subgrid add_GMCs()
        # 3) both stars and gas particles must be > 64 particles each.
        if gas_SFR.sum() <= 0.1:
            print("SFR too low.. Skipping ", galname)
            continue

        if (gas_m * gas_f_H2).sum() <= 1.e5:
            print ("Dense gas mass less than 10^5 Msun.. Skipping ", galname)
            continue

        if len(gal.slist) < 64 or len(gal.glist) < 64:
            print("Too few star particles or gas particles, unlikely to be real galaxy or useful for our purpose. Skipping ", galname)
            continue

        star_m = group_part_by_galaxy(star_p_m, gal, ptype='star')
        star_pos = group_part_by_galaxy(star_pos_p, gal, ptype='star') #/obj.simulation.boxsize
        star_pos -= loc.d
        star_vel = group_part_by_galaxy(star_vel_p, gal, ptype='star')

        if caesarRotate:
            star_pos = caesar.utils.rotator(star_pos,
                               np.float64(gal.rotation_angles['ALPHA']),
                               np.float64(gal.rotation_angles['BETA']))

            star_vel = caesar.utils.rotator(star_vel,
                                np.float64(gal.rotation_angles['ALPHA']),
                                np.float64(gal.rotation_angles['BETA']))

            star_x = ff(star_pos[:, 0])
            star_y = ff(star_pos[:, 1])
            star_z = ff(star_pos[:, 2])

            star_vx = ff(star_vel[:,0].d)
            star_vy = ff(star_vel[:,1].d)
            star_vz = ff(star_vel[:,2].d)
        else:
            star_x = star_pos[:, 0]
            star_y = star_pos[:, 1]
            star_z = star_pos[:, 2]

            star_vx = star_vel[:,0]
            star_vy = star_vel[:,1]
            star_vz = star_vel[:,2]

        star_Z =  group_part_by_galaxy(pmetarray, gal, ptype='star')

        # derive stellar age
        star_a = group_part_by_galaxy(sage, gal, ptype='star')
        current_time = obj.simulation.time.in_units("Myr")
        # in scale factors, do as with Illustris
        star_formation_z = 1. / star_a - 1
        # Code from yt project (yt.utilities.cosmology)
        star_formation_t = 2.0 / 3.0 / np.sqrt(1 - obj.simulation.omega_matter) * np.arcsinh(np.sqrt(
            (1 - obj.simulation.omega_matter) / obj.simulation.omega_matter) / np.power(1 + star_formation_z, 1.5)) / (h)  # Mpc*s/(100*km)
        star_formation_t *=  kpc2m / 100. / (1e6 * 365.25 * 86400)  # Myr
        star_age = current_time.d - star_formation_t

        # create empty DM data
        dm_m = 0.0

        dm_posx = np.array([0.0])
        dm_posy = np.array([0.0])
        dm_posz = np.array([0.0])

        dm_velx = np.array([0.0])
        dm_vely = np.array([0.0])
        dm_velz = np.array([0.0])

        # create pandas DF
        simgas_path = (savepath + 'z{:.2f}').format(float(redshift)) + '_' + \
                       galname + '_sim.gas'
        simstar_path = (savepath + 'z{:.2f}').format(float(redshift)) + \
                       '_' + galname + '_sim.star'
        simdm_path = (savepath + 'z{:.2f}').format(float(redshift)) + \
                      '_' + galname + '_sim.dm'

        simgas = pd.DataFrame({'x': gas_x, 'y': gas_y, 'z': gas_z,
                               'vx': gas_vx, 'vy': gas_vy, 'vz': gas_vz,
                               'SFR': gas_SFR, 'Z': gas_Z,
                               'nH': gas_densities,
                               'Tk': gas_Tk, 'h': gas_h,
                               'f_HI1': gas_f_HI,    # atomic and molecular H
                               'f_neu': gas_f_neu,   # atomic H
                               'f_H21': gas_f_H2, 'm': gas_m,
                               'a_He': gas_Z_1, 'a_C': gas_Z_2,
                               'a_N': gas_Z_3, 'a_O': gas_Z_4,
                               'a_Ne': gas_Z_5, 'a_Mg': gas_Z_6,
                                'a_Si': gas_Z_7, 'a_S': gas_Z_8,
                                'a_Ca': gas_Z_9, 'a_Fe': gas_Z_10})
        simgas.to_pickle(simgas_path)


        simstar = pd.DataFrame({'x': star_x, 'y': star_y, 'z': star_z,
                                'vx': star_vx, 'vy': star_vy, 'vz': star_vz,
                                'Z': star_Z, 'm': star_m, 'age': star_age})
        simstar.to_pickle(simstar_path)


        # create fake DM dataframe to trick Sigame
        simdm = pd.DataFrame({'x': dm_posx, 'y': dm_posy, 'z': dm_posz,
                              'vx': dm_velx, 'vy': dm_vely, 'vz': dm_velz,
                              'm': dm_m})
        simdm.to_pickle(simdm_path)


        galName.append(galname)


''' Ways to select physically meaningful galaxies ....

ghaloall = np.array(readsnap(snap,'HaloID','gas',suppress=1,nth=nskip),dtype=int)  # FOF halo ID from snapshot
gas_select = ((gnh>0.1)&(ghaloall>0))  # selects gas to use

if gal.masses['bh'] <= 1.e6: continue    # a way to select gal w/ BH


'''
