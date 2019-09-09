'''

look at convergence between simulations based on SFR distribution at z=5.9

e.g., m50n1024 vs. m50n512

'''

import matplotlib as mpl
mpl.use('Agg')
import matplotlib
# Specify renderer
# matplotlib.use('Agg')
# Boiler-plate settings for producing pub-quality figures
# 1 point = 1/72 inch
matplotlib.rcParams.update({'figure.figsize'  : (8,5)    # inches
                            ,'font.size'       : 22      # points
                            ,'legend.fontsize' : 16      # points
                            ,'lines.linewidth' : 2       # points
                            ,'axes.linewidth'  : 2       # points
                            ,'text.usetex'     : True    # Use LaTeX to layout text
                            ,'font.family'     : "serif" # Use serifed fonts
                            ,'xtick.major.size'  : 6     # length, points
                            ,'xtick.major.width' : 2     # points
                            ,'xtick.minor.size'  : 3     # length, points
                            ,'xtick.minor.width' : 1     # points
                            ,'ytick.major.size'  : 6     # length, points
                            ,'ytick.major.width' : 2     # points
                            ,'ytick.minor.size'  : 3     # length, points
                            ,'ytick.minor.width' : 1     # points
                            ,'font.serif'      : ("Times"
                                                  ,"Palatino"
                                                  ,"Computer Modern Roman"
                                                  ,"New Century Schoolbook"
                                                  ,"Bookman")
                            ,'font.sans-serif' : ("Helvetica"
                                                  ,"Avant Garde"
                                                  ,"Computer Modern Sans serif")
                            ,'font.monospace'  : ("Courier"
                                                  ,"Computer Modern Typewriter")
                            ,'font.cursive'    : "Zapf Chancery"
})

import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import caesar
import function as fu

nrowmax = 3


def sfrf_data(zbin, ax):
    indir = 'Observations/Katsianis17_SFRF/'
    if zbin < 0.25:
        infile = indir + 'katsianis_z0.dat'
    elif zbin < 0.75:
        infile = indir + 'katsianis_z0.5.dat'
    elif zbin < 1.25:
        infile = indir + 'katsianis_z1.dat'
    elif zbin < 1.75:
        infile = indir + 'katsianis_z1.5.dat'
    elif zbin < 8.5:
        infile = indir + 'katsianis_z%g.dat' % np.round(zbin, 0)
    else:
        print('out of data range for z=', zbin)
        return
    datacolors = ['r', 'g', 'crimson']  # 0=UV, 1=Ha, 2=IR
    datalabels = ['UV data', r'$H\alpha$ data', 'IR data']  # 0=UV, 1=Ha, 2=IR
    if np.round(zbin, 0) == 6:
        datalabels[0] += '; Bouwens+15'

    datatype, z, sfr, phi, ehi, elo, factor = np.loadtxt(infile, unpack=True)
    phi *= factor
    ehi *= factor
    elo *= factor
    datatype = np.asarray(datatype.astype(int))
    for dt in (0, 1, 2):
        if dt in datatype:
            ax.errorbar(np.log10(sfr[datatype == dt]), np.log10(phi[datatype == dt]), yerr=[np.log10(phi[datatype == dt] + ehi[datatype == dt]) - np.log10(phi[datatype == dt]), np.log10(phi[datatype == dt]) - np.log10(phi[datatype == dt] - elo[datatype == dt])],
                fmt='o', ms=5, elinewidth=1,
                label=datalabels[dt], color=datacolors[dt])
    return


def massFunc(objs, labels, ax, jwind):
    for j in range(0, len(objs)):
        for curType in TYPES:
            galpos = np.array([g.pos.d for g in objs[j].galaxies])
            if curType == 'GSMF':
                mass = np.array(
                    [g.masses['stellar'].d for g in objs[j].galaxies])
            elif curType == 'HI':
                mass = np.array([g.masses['HI'].d for g in objs[j].galaxies])
            elif curType == 'H2':
                mass = np.array([g.masses['H2'].d for g in objs[j].galaxies])
            elif curType == 'SFR':
                mass = np.array([g.sfr.d for g in objs[j].galaxies])
            elif curType == 'Halo':
                mass = np.array([h.masses['virial'].d for h in objs[j].halos])
                galpos = np.array([h.pos.d for h in objs[j].halos])

            # remove SFR = 0.0
            mask = mass > 0
            mass = mass[mask]
            galpos = galpos[mask, :]

            volume = objs[j].simulation.boxsize.to('Mpccm').d**3
            x, y, sig = fu.cosmic_variance(
                mass, galpos, objs[j].simulation.boxsize, volume, nbin=16, minmass=-3)
            ncol = int((len(objs) - 1) / nrowmax + 1)
            icol = int(j / nrowmax)
            irow = int(j % nrowmax)
            # print labels[jwind],'j=',j,'irow=',irow,'icol=',icol,'ncol=',ncol
            if ncol == 1:
                try:
                    ax0 = ax[irow]
                except:
                    ax0 = ax
            else:
                try:
                    ax0 = ax[irow][icol]
                except:
                    ax0 = ax
            # if jwind == 0:
            #     ltype = '-'
            # else:
            #     ltype = '--'
            # ax0.plot(np.log10(x) + j * 0.001, np.log10(y), ltype,
            #          color=colors[j], label=labels[j])
            elo = sig
            ehi = sig
            ax0.errorbar(np.log10(x) + j * 0.001, np.log10(y),
                         yerr=[elo, ehi], color=colors[j], label=labels[j])

    sfrf_data(objs[j].simulation.redshift, ax0)
    ax0.legend(loc='best', fontsize=13)
    # ax0.annotate('z=%g' % np.round(objs[j].simulation.redshift, 1), xy=(
    #     0.8, 0.75), xycoords='axes fraction', size=12, bbox=dict(boxstyle="round", fc="w"))
    plt.title(r'$z$ = %g' % np.round(objs[j].simulation.redshift, 1))
    return None

colors = ('b', 'g', 'm', 'c', 'k')
simName = ['m25n256', 'm25n1024', 'm50n512', 'm50n1024', 'm100n1024']

sims = []
labels = []
for ii, nn in enumerate(simName):
    if nn == 'm25n1024':
        caesarfile = '/mnt/ceph/users/daisyleung/simba/sim/' + nn + '/s50_new/Groups/' + nn + '_036.hdf5'

    else:
        caesarfile = '/mnt/ceph/users/daisyleung/simba/sim/' + nn + '/s50/Groups/' + nn + '_036.hdf5'
    sims.append(caesar.load(caesarfile, LoadHalo=False))
    labels.append(nn)

ncol = 1
nrow = 1

fig, ax = plt.subplots()
TYPES = ['SFR']
massFunc(sims, labels, ax, ii)


plt.minorticks_on()
plt.xlabel(r'$\log$ SFR $[M_\odot$ yr$^{-1}]$', fontsize=16)
plt.ylabel(r'$\log \Phi$ [Mpc$^{-3}$]',fontsize=16)
plt.xlim(-3, 3)
plt.subplots_adjust(hspace=.0)

figname = 'sfrfcn_test.pdf'
plt.savefig(figname, bbox_inches='tight')




