import caesar
import numpy as np
import cPickle as pickle
import socket
import os
import sys
from readgadget import readsnap

def info(obj, snapFile, top=None, savetxt=False):
    """
    Customized version to print more info on the CAESAR extracted galaxies.

    Parameters
    ----------
    obj : :class:`main.CAESAR`
        Main CAESAR object.
    top : int
        Number of objects to print.

    """

    group_list = obj.galaxies
    nobjs = len(group_list)

    if top > nobjs or top is None:
        top = nobjs

    if obj.simulation.cosmological_simulation:
        time = 'z=%0.3f' % obj.simulation.redshift
    else:
        time = 't=%0.3f' % obj.simulation.time

    output  = '##\n'
    output += '## Largest %d Galaxies \n' % (top)
    if hasattr(obj, 'data_file'): output += '## from: %s\n' % obj.data_file
    output += '## %d @ %s' % (nobjs, time)
    output += '##\n'
    output += '##\n'

    cnt = 1

    output += '## ID      Mstar     Mgas      MBH    fedd    SFR [Msun/yr]      SFRSD [Msun/yr/kpc^2]    r_baryon   r_gas      r_gas_half_mass      r_stellar    r_stellar_half_mass    Z_sfrWeighted [/Zsun]    Z_massWeighted     Z_stellar     T_gas_massWeighted    T_gas_SFRWeighted   fgas   nrho      Central\t|  Mhalo     HID\n'
    output += '## ----------------------------------------------------------------------------------------\n'

    h = obj.simulation.hubble_constant
    bhmdot = readsnap(snapFile, 'BH_Mdot','bndry',suppress=1)*1.e10/h/3.08568e+16*3.155e7 # in Mo/yr

    # debug mbh:
    # mmm = [g.masses['bh'] for g in obj.galaxies]
    # mmm[:10]

    for ii, o in enumerate(group_list):
        phm, phid = -1, -1

        if o.halo is not None:
            phm, phid = o.halo.masses['total'], o.halo.GroupID

        try:
            bhmdots = [bhmdot[k] for k in o.bhlist]
            bm = o.masses['bh']
            imax = np.argmax(bm)
            try:
                bm = bm[imax]
                bmdot = bhmdots[imax]        # only the massive BH particle matters.
            except:
                bm = bm
                bmdot = bhmdots
            frad = 0.1
            mdot_edd = 4*np.pi*6.67e-8*1.673e-24/(frad*3.e10*6.65245e-25) * bm * 3.155e7 # in Mo/yr
            fedd = bmdot / mdot_edd
            fedd = fedd[0].value
        except:
            bm = 0
            fedd = 0

        # print bm, fedd
        # import pdb; pdb.set_trace()

        output += ' %04d  %0.2e  %0.2e  %0.2e  %0.2e  %0.2e  %0.2e  %0.2e  %0.2e  %0.2e  %0.2e  %0.2e   %0.3f   %0.3f  %0.3f  %0.2e  %0.2e  %0.3f  %0.2e  %s\t|  %0.2e  %d \n' % \
                  (o.GroupID, o.masses['stellar'], o.masses['gas'],
                   bm,
                   fedd,
                   o.sfr,
                   o.sfr/np.pi/o.radii['gas']**2,
                   o.radii['baryon'],
                   o.radii['gas'],
                   o.radii['gas_half_mass'],
                   o.radii['stellar'],
                   o.radii['stellar_half_mass'],
                   o.metallicities['sfr_weighted']/0.0134,
                   o.metallicities['mass_weighted'],
                   o.metallicities['stellar'],
                   o.temperatures['mass_weighted'],
                   o.temperatures['sfr_weighted'],
                   o.gas_fraction,
                   o.local_number_density, o.central,
                   phm, phid)

        cnt += 1
        if cnt > top: break

    print(output)

    if savetxt:

        outputFileName = snapFile[50:-5] + '_top' + str(top) + '.txt'
        f = open(outputFileName, 'w')
        f.write(output)
        f.close()

    return output, outputFileName


def setup_cmap(cm='magma'):    # "plasma_r"
    import matplotlib.pyplot as plt
    return plt.set_cmap(cm)


def setup_plot():
    import matplotlib
    from cycler import cycler
    # print(matplotlib.matplotlib_fname())

    matplotlib.rcParams.update({'figure.figsize': (8, 5)    # inches
                                , 'font.size': 16      # points
                                , 'legend.fontsize': 10      # points
                                , 'lines.linewidth': 2       # points
                                , 'axes.linewidth': 1       # points
                                , 'axes.prop_cycle': cycler('color', 'bgrcmyk')
                                , 'text.usetex': True
                                , 'font.family': "serif"  # Use serifed fonts
                                , 'xtick.major.size': 13     # length, points
                                , 'xtick.major.width': 1     # points
                                , 'xtick.minor.size': 8     # length, points
                                , 'xtick.minor.width': 1     # points
                                , 'ytick.major.size': 13     # length, points
                                , 'ytick.major.width': 1     # points
                                , 'ytick.minor.size': 8     # length, points
                                , 'xtick.labelsize': 14
                                , 'ytick.labelsize': 14
                                , 'ytick.minor.width': 1     # points
                                , 'font.serif': ("times", "Computer Modern Roman", "New Century Schoolbook", "Bookman"), 'font.sans-serif': ("Helvetica", "Avant Garde", "Computer Modern Sans serif"), 'font.monospace': ("Courier", "Computer Modern Typewriter"), 'font.cursive': "Zapf Chancery"
                                })
    cm = setup_cmap()
    return cm


def plot_info(colNumx, colNumy, inFile,
              colNumz=None, zlabel='',
              logx=True, logy=True, logz=True,
              xlabel='',
              ylabel='',
              ls='',
              marker='*',
              markersize=10,
              legendFontSize=17,
              cbarLabelSize=17,
              tag='',
              saveFig=True, savedir='../plots/'):
    """

    colNumx: int
        column to read from the .txt file, used as x-axis in plotting

    colNumy: int
        column to read from the .txt file, used as y-axis in plotting

    colNumz: int
        column to read from the .txt file, used as color in plotting

    inFile: str
        name of input file to read from where we extract global properties of galaxies


    """

    colNumx = int(colNumx)
    colNumy = int(colNumy)
    xxx, yyy = np.genfromtxt(inFile, usecols=(colNumx, colNumy), unpack=True)

    import matplotlib.pyplot as plt
    cm = setup_plot()
    plt.close('all')
    fig = plt.figure()
    ax = fig.add_subplot(111)

    if colNumz:
        fig.subplots_adjust(right=0.84, wspace=0.01)
        colNumz = int(colNumz)
        zzz = np.genfromtxt(inFile, usecols=(colNumz))

        cm = plt.get_cmap()

        if logz:
            if zzz.min() == 0.0:
                zzz += 1.e-6

            c = list(np.log10(zzz))

        else:
            c = list(zzz)

        cmap = matplotlib.cm.get_cmap('viridis')
        normalize = matplotlib.colors.Normalize(vmin=min(c), vmax=max(c))
        colors = [cmap(normalize(value)) for value in c]
        # NUM_COLORS = len(c)
        # ax.set_prop_cycle('color', [cm(1. * i / NUM_COLORS)
        #                             for i in range(NUM_COLORS)])

        ax.scatter(xxx, yyy, color=colors, s=markersize,
                 marker=marker)

    else:
        ax.plot(xxx, yyy, ls=ls, markersize=markersize,
                 marker=marker, color='k',
                 # markeredgecolor='gray',
                 markeredgewidth=0.5)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.minorticks_on()

    if colNumz:
        cax, _ = matplotlib.colorbar.make_axes(ax)
        cbar = matplotlib.colorbar.ColorbarBase(cax, cmap=cmap, norm=normalize)

        cbar.ax.tick_params(length=6, labelsize=legendFontSize)
        cbar.set_label(zlabel, fontsize=cbarLabelSize)

    if not saveFig:
        plt.show(block=False)
    else:
        # fig.subplots_adjust(right=0.84, left=0.1, top=0.85,
        #                     bottom=0.1, hspace=0.2,
        #                     wspace=0.1)
        if not os.path.isdir(savedir):
            os.makedirs(savedir)

        figName = savedir + xlabel + '_' + ylabel
        if colNumz:
            figName += '_' + zlabel
        if len(tag) > 0:
            figName += '_' + tag + '_'
        figName += '.png'
        plt.savefig(figName, bbox_inches='tight')

    return fig, ax


if __name__ == '__main__':

    if len(sys.argv) > 1:
        debug = sys.argv[1]
        LoadHalo = False
    else:
        debug = False
        LoadHalo = True

    snapRange = [36]    # don't put 036
    zCloudy = 6
    raw_sim_name_prefix = 'snap_m25n1024_'
    name_prefix = 'm25n1024_'

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

        if 'worker' in host:
            import matplotlib
            matplotlib.use('Agg')

    infile = caesar_dir + name_prefix + '{:0>3}'.format(int(36)) + \
                '.hdf5'
    obj = caesar.load(infile, LoadHalo=LoadHalo)
    snapFile = raw_sim_dir + raw_sim_name_prefix + '{:0>3}'.format(int(36)) + '.hdf5'

    output, outName = info(obj, snapFile, top=None, savetxt=True)
    savedir='../plots/' + str(outName[:outName.find('.txt')]) + '/'

    fig, ax = plot_info(1, 20, inFile=outName, colNumz=17, zlabel='fgas',
                        xlabel='Mstar', ylabel='Mhalo',
                        savedir=savedir)

    fig, ax = plot_info(2, 1, inFile=outName, colNumz=3, xlabel='Mgas', \
                        ylabel='Mstar', zlabel='MBH', savedir=savedir)

    fig, ax = plot_info(2, 1, inFile=outName, colNumz=5, xlabel='Mgas', \
                        ylabel='Mstar', zlabel='SFR', savedir=savedir)

    # MZR:
    fig, ax = plot_info(1, 14, inFile=outName, colNumz=12, xlabel='Mstar', \
                    ylabel='Zstellar', zlabel='Zgas', savedir=savedir)

    fig, ax = plot_info(1, 12, inFile=outName, colNumz=17, xlabel='Mstar', \
                    ylabel='Zgas', zlabel='fgas', savedir=savedir)

    # FMR: SFR - Z - M*
    fig, ax = plot_info(5, 12, inFile=outName, colNumz=1, xlabel='SFR', \
                    ylabel='Zgas', zlabel='Mstar', savedir=savedir)

    # SFR f_gas
    fig, ax = plot_info(5, 17, inFile=outName, colNumz=1, xlabel='SFR', \
                    ylabel='fgas', zlabel='Mstar', savedir=savedir)

    fig, ax = plot_info(6, 17, inFile=outName, colNumz=7, xlabel='SFRSD', \
                    ylabel='f_gas', zlabel='R', savedir=savedir)

    exit()



