#!/usr/bin/env python
# vim: set ai ts=4 sw=4 sts=4 noet fileencoding=utf-8 ft=python

'''
This python script is intended to run the complete simulation process
for a number of events defined during runtime.
If you wish you can also include the reconstruction with AcquRoot as
well as the particle sorting with GoAT.

To execute this script, check that all programs are installed properly
and set the variables accordingly. When this is done, make sure the
file is executable (chmod +x run.py) and type:
./run.py
It is also possible to provide a config file with everything which
should be simulated like the example channel_config, simply run
./run.py channel_config
'''

# IMPORTANT!
# Change the paths where the data is stored to your needs and make sure
# to change the AcquRoot and GoAT paths if switched on with RECONSTRUCT
#DATA_OUTPUT_PATH = "~/MC"
DATA_OUTPUT_PATH = '~/git/simulation_chain'
PLUTO_DATA = "sim_data"  # relative path to DATA_OUTPUT_PATH where the Pluto data should be stored
GEANT_DATA = "g4_sim"  # relative path to DATA_OUTPUT_PATH where the Geant4 simulated data should be stored
A2_GEANT_PATH = "~/git/a2geant"
RECONSTRUCT = True
#ACQU_PATH = "~/acqu"
#ACQU_BUILD = "~/acqu/build"
ACQU_PATH = "~/git/acqu_a2dev"
ACQU_BUILD = "~/git/acqu_a2dev/build"
ACQU_CONFIG = "data/AR.MC"  # relative path to acqu_user directory in ACQU_PATH
ACQU_DATA = "acqu"  # relative path to DATA_OUTPUT_PATH where the AcquRoot reconstructed data should be stored
GOAT_PATH = "~/git/a2GoAT"
GOAT_BUILD = "~/git/a2GoAT/build"
GOAT_CONFIG = "configfiles/GoAT-Convert.dat"  # relative path to GOAT_PATH
GOAT_DATA = "goat"  # relative path to DATA_OUTPUT_PATH where the GoAT sorted data should be stored
MERGED_DATA = "merged"  # relative path to DATA_OUTPUT_PATH where the merged data (Goat + Pluto + Geant) should be stored
# optional settings for smearing generated Pluto data
SMEAR_Z_VERTEX = True
Z_VERTEX_SMEARING = 10  # unit in cm
SMEAR_BEAM_POSITION = True
BEAM_SMEARING = 2  # diameter for beam smearing, unit in cm

# End of user changes

import os, sys
import re
import errno
import logging
import datetime
import subprocess
import fileinput
from shutil import copyfile, move
from os.path import join as pjoin
# import module which provides colored output
from color import *

# paths for later usage
pluto_data = ''
geant_data = ''
acqu_user = ''
acqu_bin = ''
acqu_data = ''
goat_bin = ''
goat_data = ''
merged_data = ''
current_file = ''

# lists of currently available simulation files
pluto_files = []
mkin_files = []
geant_files = []


logging.setLoggerClass(ColoredLogger)
logger = logging.getLogger('Simulation')
#logger.setLevel(logging.DEBUG)

channels = [
    'etap_e+e-g',
    'etap_pi+pi-eta',
    'etap_rho0g',
    'etap_mu+mu-g',
    'etap_gg',
    'eta_e+e-g',
    'eta_pi+pi-g',
    'eta_pi+pi-pi0',
    'eta_mu+mu-g',
    'eta_gg',
    'omega_e+e-pi0',
    'omega_pi+pi-pi0',
    'omega_pi+pi-',
    'rho0_e+e-',
    'rho0_pi+pi-',
    'pi0_e+e-g',
    'pi0_gg',
    'pi+pi-pi0',
    'pi+pi-',
    'pi0pi0_4g',
    'pi0eta_4g',
    'etap_pi0pi0eta',
    'etap_pi0pi0pi0',
    'etap_pi+pi-pi0',
    'etap_omegag',
    'omega_etag'
]

def check_path(path, create=False):
    path = os.path.expanduser(path)
    exist = os.path.isdir(path)
    if not exist and create:
        print("Directory '%s' does not exist, it will be created now" % path)
        # try to create the directory; if it should exist for whatever reason,
        # ignore it, otherwise report the error
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno == errno.EACCES:
                print_error("[ERROR] You don't have the permission to create directories in '%s'" % os.path.dirname(path))
                return False
            elif exception.errno != errno.EEXIST:
                raise
        return True
    elif not exist:
        print_error("[ERROR] Directory '%s' does not exist" % path)
        return False
    else:
        return True

def check_file(path, file):
    path = os.path.expanduser(path)
    if file is None:
        if not os.path.isfile(path):
            print_error("[ERROR] The file '%s' does not exist!" % (path))
            return False
        else:
            return True
    if not os.path.isfile(get_path(path, file)):
        print_error("[ERROR] The file '%s' does not exist!" % (path + file))
        return False
    else:
        return True

def check_permission(path, permission):
    if check_path(path):
        return os.access(path, permission)
    else:
        return False

def is_readable(path):
    return check_permission(path, os.R_OK)

def is_writeable(path):
    return check_permission(path, os.W_OK)

def format_channel(channel, spaces=True):
    replace = [
        ('etap', 'eta\''),
        ('eta', 'η'),
        ('mu', 'µ'),
        ('pi', 'π'),
        ('omega', 'ω'),
        ('rho', 'ρ'),
        ('g', 'γ'),
        ('0', '⁰'),
        ('+', '⁺'),
        ('-', '⁻')
    ]

    for i, j in replace:
        channel = channel.replace(i, j)

    if spaces:
        chan = re.split(r'_', channel)

        try:
            channel = "  {0:<4s} -->  {1}".format(*chan)
        except:
            channel = "  " + channel
    else:
        channel = channel.replace('_', ' --> ')

    return channel

def unit_prefix(number):
    if number >= 1000000000:
        if str(number).count('0') >= 9:
            return re.sub(r"000000000$", "G", str(number))
        else:
            return str(number/1E9) + 'G'
    elif number >= 1000000:
        if str(number).count('0') >= 6:
            return re.sub(r"000000$", "M", str(number))
        else:
            return str(number/1E6) + 'M'
    elif number >= 1000:
        if str(number).count('0') >= 3:
            return re.sub(r"000$", "k", str(number))
        else:
            return str(number/1E3) + 'k'
    else:
        return str(number)

def input_int(message):
    n = input(message + ' ')

    if not n.isdigit():
        print_error("[ERROR] Invalid input! Please make sure to enter only numbers.")
        raise ValueError('Invalid input submitted')

    return int(n)

def max_file_number(lst):
    if not lst:
        return 0
    n = re.compile(r'^.+_(\d+)(_mkin)?\..*$')
    nrs = [int(n.search(l).group(1)) for l in lst if n.search(l) is not None]
    nrs.sort()
    if not nrs:
        return 0
    else:
        return nrs[-1]

def get_path(path, file):
    return os.path.expanduser(pjoin(path, file))

def replace_all(file, search_exp, replace_exp, number_replacements=0):
    if number_replacements < 0:
        raise ValueError('Negative number of replacements submitted')

    if number_replacements:
        counter = 0
    for line in fileinput.input(file, inplace=True):
        if search_exp in line:
            if number_replacements:
                if counter == number_replacements:
                    continue
                else:
                    counter += 1
            line = replace_exp
            #line = line.replace(search_exp, replace_exp)
        print(line, end='')

def replace_line(file, search_exp, replace_exp):
    replace_all(file, search_exp, replace_exp, 1)

def run(cmd, logfile, error=False):
    if error:
        p = subprocess.Popen(cmd, shell=True, universal_newlines=True, stdout=logfile, stderr=logfile)
    else:
        p = subprocess.Popen(cmd, shell=True, universal_newlines=True, stdout=logfile)
    #ret_code = p.wait()
    #logfile.flush()
    return p.wait()

def timestamp():
    return '[%s] ' % str(datetime.datetime.now()).split('.')[0]

def write_current_info(string):
    try:
        with open(current_file, 'w') as f:
            f.write(string)
    except:
        raise

# do some kind of sanity check if the existing simulation files seem to be okay and return the maximum file number
def check_simulation_files(channel):
    pluto_channel = [f for f in pluto_files if channel in f]
    mkin_channel = [f for f in mkin_files if channel in f]
    geant_channel = [f for f in geant_files if channel in f]
    max_pluto = max_file_number(pluto_channel)
    max_mkin = max_file_number(mkin_channel)
    max_geant = max_file_number(geant_channel)
    maximum = max_pluto
    if max_pluto > max_mkin:
        print_color("\tWarning", RED)
        print("Maybe there are some files for channel %s that\naren't converted yet (and hence simulated with Geant4)"
                % format_channel(channel, False))
        input("Will continue by pressing any key ")
        maximum = max_pluto
    elif max_mkin > max_pluto:
        print_color("\tWarning", RED)
        print("There are more converted files than Pluto generated ones\nfor channel %s – proceed at your own risk"
                % format_channel(channel, False))
        input("Will continue by pressing any key ")
        maximum = max_mkin
    if max_geant > maximum:
        print_color("\tWarning", RED)
        print("There are more Geant4 simulation files than Pluto generated\nfiles for channel %s"
                % format_channel(channel, False))
        input("Will continue by pressing any key ")
        maximum = max_geant
    elif max_geant < maximum:
        print_color("\tWarning", RED)
        print("There are more Pluto generated files than Geant4 simulated\nfiles for channel %s"
                % format_channel(channel, False))
        input("Will continue by pressing any key ")

    return maximum

def list_file_amount(events=False):
    print('Amount of simulated %s per channel:' % ('events' if events else 'files'))
    for channel in channels:
        pluto_channel = [f for f in pluto_files if channel in f]
        mkin_channel = [f for f in mkin_files if channel in f]
        geant_channel = [f for f in geant_files if channel in f]
        max_pluto = max_file_number(pluto_channel)
        max_mkin = max_file_number(mkin_channel)
        max_geant = max_file_number(geant_channel)
        maximum = max(max_pluto, max_mkin, max_geant)
        if maximum > 0:
            if not events:
                print(' {0:<20s} -- {1:>3d} files'.format(format_channel(channel), maximum))
            # assume every file contains the same amount of events, pick mkin files for event numbers
            else:
                sum = 0
                from ROOT import TFile, TTree, TH1
                for f in mkin_channel:
                    filename = get_path(pluto_data, f)
                    current = TFile(filename)
                    if not current.IsOpen():
                        print_error("The file '%s' could not be opened" % filename)
                        continue
                    elif not current.GetListOfKeys().GetSize():
                        print_error("Found no directory in file '%s'" % current.GetName())
                        continue
                    name = current.GetListOfKeys().First().GetName()
                    tree = current.Get(name)
                    sum += tree.GetEntriesFast()
                print(' {0:<20s} -- {1:>3d} files,  total {2:>8s} events'.format(format_channel(channel), maximum, unit_prefix(sum)))

# check if all the needed path and files exist
def check_paths():
    # check if the given output path exists
    if not check_path(DATA_OUTPUT_PATH):
        print("        Please make sure the specified output directory exists.")
        return False

    # check if the A2 Geant4 executable exists in the given path
    # (created this way when the a2geant git repo is used)
    if not check_path(A2_GEANT_PATH):
        print("        Please make sure your Geant4 installation can be found within the specified path.")
        return False
    elif not check_file(A2_GEANT_PATH, 'A2'):
        print("        A2 Geant4 executable not found in '%s'." % A2_GEANT_PATH)
        return False
    # check target length in A2 Geant4 DetectorSetup.mac
    if SMEAR_Z_VERTEX:
        geant_macros = get_path(A2_GEANT_PATH, 'macros')
        if not check_file(geant_macros, 'DetectorSetup.mac'):
            print("        No 'DetectorSetup.mac' macro found in the Geant macros directory.")
            return False
        target_length = ''
        with open(get_path(geant_macros, 'DetectorSetup.mac'), 'r') as mac:
            for line in mac:
                if '/A2/det/setTargetLength' in line:
                    target_length = line.split()[1]
        if float(target_length) < Z_VERTEX_SMEARING:
            print_color("[WARNING] The target length specified in the 'DetectorSetup.mac' macro", RED)
            print_color('          in your Geant macros directory is smaller than your specified', RED)
            print_color('          z vertex smearing. Geant will correct the z vertex in order to', RED)
            print_color('          fit into the target length of %s cm. Modify the target length' % target_length, RED)
            print_color('          if you want to use the vertex smearing of %.2f cm' % Z_VERTEX_SMEARING, RED)
            print()

    # needed to modify global variables within this function
    global pluto_data, geant_data, acqu_user, acqu_bin, acqu_data, goat_bin, goat_data, merged_data

    # create folders to store Pluto and Geant4 data if not existing
    pluto_data = DATA_OUTPUT_PATH
    geant_data = pluto_data[:]  # copy the string
    pluto_data = get_path(pluto_data, PLUTO_DATA)
    if not check_path(pluto_data, True):
        print("        Please make sure the Pluto output directory exists or could be created and is accessable as well.")
        return False
    geant_data = get_path(geant_data, GEANT_DATA)
    if not check_path(geant_data, True):
        print("        Please make sure the Geant output directory exists or could be created and is accessable as well.")
        return False
    # check if the pluto2mkin converter is available
    if not check_file(A2_GEANT_PATH, 'pluto2mkin'):
        print("        No pluto2mkin executable in the Geant directory found.")
        print("        Please make sure it is there or build it otherwise.")
        return False

    if RECONSTRUCT:
        # first check if AcquRoot is ready to run
        if not check_path(ACQU_PATH):
            print("        Please make sure your acqu directory can be found at the given path.")
            return False
        acqu_user = get_path(ACQU_PATH, 'acqu_user')
        if not check_path(acqu_user):
            print("        Please make sure you installed acqu properly.")
            return False
        acqu_bin = get_path(ACQU_BUILD, 'bin')
        if not check_file(acqu_bin, 'AcquRoot'):
            print("        Could not find the main AcquRoot executable.")
            print("        Please make sure you installed acqu properly.")
            return False
        if not check_file(acqu_user, ACQU_CONFIG):
            print("        Could not find your specified AcquRoot config file.")
            return False
        acqu_config_dir = pjoin(acqu_user, os.path.dirname(ACQU_CONFIG))
        acqu_data = get_path(DATA_OUTPUT_PATH, ACQU_DATA)
        if not check_path(acqu_data, True):
            print("        Please make sure the AcquRoot output directory exists or could be created and is accessable as well.")
            return False
        # check if AcquRoot is configured to execute TA2GoAT
        with open(get_path(acqu_user, ACQU_CONFIG), 'r') as file:
            for line in file:
                if 'AnalysisSetup:' in line:
                    acqu_analysis = line.split()[-1]  # split spaces, tabs, newlines and take last entry of list
        with open(get_path(acqu_config_dir, acqu_analysis), 'r') as file:
            for line in file:
                if 'Physics-Analysis:' in line and not '#Physics-Analysis:' in line:
                    if 'TA2GoAT' not in line:
                        print_color("[ERROR] Specified analysis class in AcquRoot config '%s'" % acqu_analysis, RED)
                        print_color("        is not TA2GoAT. Can't create files for GoAT this way.", RED)
                        return False

        # now check GoAT
        if not check_path(GOAT_PATH):
            print("        Please make sure your goat directory can be found at the given path.")
            return False
        goat_bin = get_path(GOAT_BUILD, 'bin')
        if not check_file(goat_bin, 'goat'):
            print("        Could not find the main goat executable.")
            print("        Please make sure you installed GoAT properly.")
            return False
        goat_bin = os.path.expanduser(goat_bin)
        if not check_file(GOAT_PATH, GOAT_CONFIG):
            print("        Could not find your specified goat config file.")
            return False
        goat_data = get_path(DATA_OUTPUT_PATH, GOAT_DATA)
        if not check_path(goat_data, True):
            print("        Please make sure the GoAT output directory exists or could be created and is accessable as well.")
            return False

        # finally check directory for merged output
        merged_data = get_path(DATA_OUTPUT_PATH, MERGED_DATA)
        if not check_path(merged_data, True):
            print("        Please make sure the output directory for merged files exists or could be created and is accessable as well.")
            return False

    return True

def prepare_acqu():
    config_org = pjoin(acqu_user, ACQU_CONFIG)
    acqu_configs = os.path.dirname(config_org)
    config_new = pjoin(acqu_configs, 'AR.sim_chain')
    if check_file(config_new, None):
        for line in fileinput.input(config_new, inplace=True):
            if 'Directory:' in line:
                line = 'Directory:\t%s\n' % acqu_data
            print(line, end='')
        return config_new
    copyfile(config_org, config_new)

    with open(config_new, 'r+') as f:
        lines = [line for line in f.readlines() if 'TreeFile:' not in line and 'Directory:' not in line]
        # find output directory and change it
        f.seek(0)  # go to the beginning of the file
        f.writelines(lines)
        f.truncate()  # resize stream --> avoid race conditions (rest of the old file occuring at the end of the new one)
        f.write('\nDirectory:\t%s\n' % acqu_data)
        f.write('\nTreeFile:\tpath/file.root\n')
    return config_new

def pluto_simulation(amount, sim_log):
    total = sum(files*events for _, files, events, _ in amount)
    print_color('\nStarting Pluto simulation for total %s events\n' % unit_prefix(total), RED)
    sim_log.write('\n' + timestamp() + 'Starting Pluto simulation for total %s events\n' % unit_prefix(total))
    with open(get_path(DATA_OUTPUT_PATH, 'pluto.log'), 'w') as log:
        for index, (channel, files, events, number) in enumerate(amount, start=1):
            print_color('Processing channel %s' % format_channel(channel, False), GREEN)
            sim_log.write('\n' + timestamp() + 'Processing channel %s\n' % format_channel(channel, False))
            for i in range(number+1, number+1+files):  # number is the highest existing file number, start with number+1, for end of range add number of files
                logger.info('Generating file %s/sim_%s_%02d.root with %d events' % (pluto_data, channel, i, events))
                sim_log.write(timestamp() + 'Generating file %s/sim_%s_%02d.root with %d events\n' % (pluto_data, channel, i, events))
                sim_log.flush()
                current = timestamp()
                current += "Pluto simulation, channel %s (%d/%d), file %02d (%d/%d)" % (channel, index, len(amount), i, i-number, files)
                write_current_info(current)
                f = open('sim.C', 'w')
                f.write('sim(){ gROOT->ProcessLine(".x simulate.C(%d, %d, \\\"%s\\\", \\\"%s\\\")"); }' % (events, i, channel, pluto_data))
                f.close()
                cmd = 'root -l sim.C'
                # due to ROOT's double free curruption errors, pipe sys.stderr to pluto.log
                ret = run(cmd, log, True)  # let Pluto print errors to the logfile as well because it prints normal information to stderr
                if ret:
                    logger.critical('Non-zero return code (%d), something might have gone wrong' % ret)
                    sim_log.write(timestamp() + 'Non-zero return code (%d), something might have gone wrong\n' % ret)
                    sim_log.flush()
    print_color('\nFinished Pluto simulation\n', RED)
    sim_log.write('\n' + timestamp() + 'Finished Pluto simulation\n\n')

def mkin_conversion(amount, sim_log):
    n_files = sum(files for _, files, _, _ in amount)
    print_color('\nConversion of the %d Pluto-generated files\n' % n_files, RED)
    sim_log.write('\n' + timestamp() + 'Conversion of the %d Pluto-generated files\n' % n_files)
    cmd = get_path(A2_GEANT_PATH, 'pluto2mkin')
    ''' The vertex position can be smeared according to the target length (z vertex)
        and the beam diameter (x and y vertices)
        The z smearing is uniform, x and y are gaussian shaped. The values can be changed
        in the top section of the file. '''
    if SMEAR_Z_VERTEX:
        cmd += ' --target length=%f' % Z_VERTEX_SMEARING
    if SMEAR_BEAM_POSITION:
        cmd += '  --beam diam=%f' % BEAM_SMEARING
    with open(get_path(DATA_OUTPUT_PATH, 'mkin.log'), 'w') as log:
        for index, (channel, files, events, number) in enumerate(amount, start=1):
            for i in range(number+1, number+1+files):
                current = timestamp()
                current += "Converting files for Geant, channel %s (%d/%d), file %02d (%d/%d)" % (channel, index, len(amount), i, i-number, files)
                write_current_info(current)
                run(cmd + " --input %s/sim_%s_%02d.root" % (pluto_data, channel, i), log, True)  # mkin converter prints warning because of missing dictionary for PParticle to stderr
                #run(cmd + " --input %s/%s_%02d.root --target length=10 --beam diam=2" % (pluto_data, channel, i), log)
                # move the mkin file to the pluto simulation data directory
                move('%s/sim_%s_%02d_mkin.root' % (os.getcwd(), channel, i), '%s/sim_%s_%02d_mkin.root' % (pluto_data, channel, i))
    print_color('\nFinished converting the files\n', RED)
    sim_log.write('\n' + timestamp() + 'Finished converting the files\n\n')

def geant_simulation(amount, sim_log):
    print_color('\n - - - Starting detector simulation - - - \n', RED)
    sim_log.write('\n' + timestamp() + ' - - - Starting detector simulation - - - \n')
    cmd = get_path(A2_GEANT_PATH, 'A2')
    cmd += ' macros/vis.mac'
    macro = get_path(A2_GEANT_PATH, 'macros/g4run_multi.mac')
    wd = os.getcwd()
    os.chdir(os.path.expanduser(A2_GEANT_PATH))
    with open(get_path(DATA_OUTPUT_PATH, 'geant.log'), 'w') as log:
        for index, (channel, files, events, number) in enumerate(amount, start=1):
            print_color('Processing channel %s' % format_channel(channel, False), GREEN)
            sim_log.write('\n' + timestamp() + 'Processing channel %s\n' % format_channel(channel, False))
            macro_channel = get_path(wd, 'g4run/g4run_%s.mac' % channel)
            for i in range(number+1, number+1+files):
                logger.info('Performing simulation for file %s/sim_%s_%02d.root' % (pluto_data, channel, i))
                sim_log.write(timestamp() + 'Performing simulation for file %s/sim_%s_%02d.root\n' % (pluto_data, channel, i))
                sim_log.flush()
                current = timestamp()
                current += "Processing Geant simulation, channel %s (%d/%d), file %02d (%d/%d)" % (channel, index, len(amount), i, i-number, files)
                write_current_info(current)
                copyfile(macro_channel, macro)
                f = open(macro, 'a')
                f.write('/A2/generator/InputFile %s/sim_%s_%02d_mkin.root\n' % (pluto_data, channel, i))
                f.write('/A2/event/setOutputFile %s/g4_sim_%s_%02d.root\n' % (geant_data, channel, i))
                f.close()
                ret = run(cmd, log, True)  # let Geant print errors to the logfile as well because it prints warnings to stderr
                if ret:
                    logger.critical('Non-zero return code (%d), something might have gone wrong' % ret)
                    sim_log.write(timestamp() + 'Non-zero return code (%d), something might have gone wrong\n' % ret)
                    sim_log.flush()
    os.chdir(wd)
    print_color('\nFinished the detector simulation\n', RED)
    sim_log.write('\n' + timestamp() + 'Finished the detector simulation\n\n')

def acqu(amount, sim_log):
    print_color('\n - - - Starting particle reconstruction with AcquRoot - - - \n', RED)
    sim_log.write('\n' + timestamp() + ' - - - Starting particle reconstruction with AcquRoot - - - \n')
    config = prepare_acqu()
    cmd = acqu_bin + '/AcquRoot' + ' ' + os.path.dirname(ACQU_CONFIG) + '/' + config.split('/')[-1]
    wd = os.getcwd()
    os.chdir(acqu_user)
    with open(get_path(DATA_OUTPUT_PATH, 'acqu.log'), 'w') as log:
        for index, (channel, files, events, number) in enumerate(amount, start=1):
            print_color('Processing channel %s' % format_channel(channel, False), GREEN)
            sim_log.write('\n' + timestamp() + 'Processing channel %s\n' % format_channel(channel, False))
            for i in range(number+1, number+1+files):
                logger.info('Reconstructing file %s/g4_sim_%s_%02d.root' % (geant_data, channel, i))
                sim_log.write(timestamp() + 'Reconstructing file %s/g4_sim_%s_%02d.root\n' % (geant_data, channel, i))
                sim_log.flush()
                current = timestamp()
                current += "AcquRoot particle reconstruction, channel %s (%d/%d), file %02d (%d/%d)" % (channel, index, len(amount), i, i-number, files)
                write_current_info(current)
                replace_line(config, 'TreeFile:', 'TreeFile:\t%s/g4_sim_%s_%02d.root' % (geant_data, channel, i))
                ret = run(cmd, log)
                if ret:
                    logger.critical('Non-zero return code (%d), something might have gone wrong' % ret)
                    sim_log.write(timestamp() + 'Non-zero return code (%d), something might have gone wrong\n' % ret)
                    sim_log.flush()
    os.chdir(wd)
    print_color('\nFinished particle reconstruction\n', RED)
    sim_log.write('\n' + timestamp() + 'Finished particle reconstruction\n\n')

def goat(amount, sim_log):
    print_color('\n - - - Starting GoAT particle sorting - - - \n', RED)
    sim_log.write('\n' + timestamp() + ' - - - Starting GoAT particle sorting - - - \n')
    cmd = goat_bin + '/goat' + ' ' + GOAT_CONFIG + ' -d ' + acqu_data + ' -D ' + goat_data
    wd = os.getcwd()
    os.chdir(os.path.expanduser(GOAT_PATH))
    with open(get_path(DATA_OUTPUT_PATH, 'goat.log'), 'w') as log:
        for index, (channel, files, events, number) in enumerate(amount, start=1):
            print_color('Processing channel %s' % format_channel(channel, False), GREEN)
            sim_log.write('\n' + timestamp() + 'Processing channel %s\n' % format_channel(channel, False))
            for i in range(number+1, number+1+files):
                input_file = 'Acqu_g4_sim_%s_%02d.root' % (channel, i)
                logger.info('Processing file %s/%s' % (acqu_data, input_file))
                sim_log.write(timestamp() + 'Processing file %s/%s\n' % (acqu_data, input_file))
                sim_log.flush()
                current = timestamp()
                current += "GoAT particle sorting, channel %s (%d/%d), file %02d (%d/%d)" % (channel, index, len(amount), i, i-number, files)
                write_current_info(current)
                ret = run(cmd + ' -f ' + input_file, log)
                if ret:
                    logger.critical('Non-zero return code (%d), something might have gone wrong' % ret)
                    sim_log.write(timestamp() + 'Non-zero return code (%d), something might have gone wrong\n' % ret)
                    sim_log.flush()
    os.chdir(wd)
    print_color('\nFinished particle sorting\n', RED)
    sim_log.write('\n' + timestamp() + 'Finished particle sorting\n\n')

def hadd(amount, sim_log):
    print_color('\n - - - Start merging root files - - - \n', RED)
    sim_log.write('\n' + timestamp() + ' - - - Start merging root files - - - \n')
    cmd = 'hadd '
    wd = os.getcwd()
    os.chdir(os.path.expanduser(DATA_OUTPUT_PATH))
    with open('hadd.log', 'w') as log:
        for index, (channel, files, events, number) in enumerate(amount, start=1):
            print_color('Processing channel %s' % format_channel(channel, False), GREEN)
            sim_log.write('\n' + timestamp() + 'Processing channel %s\n' % format_channel(channel, False))
            for i in range(number+1, number+1+files):
                output_file = '%s/Goat_merged_%s_%02d.root' % (merged_data, channel, i)
                logger.info('Merging file %s' % output_file)
                sim_log.write(timestamp() + 'Merging file %s\n' % output_file)
                sim_log.flush()
                current = timestamp()
                current += "hadd file merging, channel %s (%d/%d), file %02d (%d/%d)" % (channel, index, len(amount), i, i-number, files)
                write_current_info(current)
                goat = '%s/GoAT_g4_sim_%s_%02d.root ' % (goat_data, channel, i)
                pluto = '%s/sim_%s_%02d.root ' % (pluto_data, channel, i)
                geant = '%s/g4_sim_%s_%02d.root' % (geant_data, channel, i)
                current_cmd = cmd + output_file + ' ' + goat + pluto + geant
                ret = run(current_cmd, log, True)  # print errors to the log file because of missing PParticle dictionary
                if ret:
                    logger.critical('Non-zero return code (%d), something might have gone wrong' % ret)
                    sim_log.write(timestamp() + 'Non-zero return code (%d), something might have gone wrong\n' % ret)
                    sim_log.flush()
    os.chdir(wd)
    print_color('\nFinished merging files\n', RED)
    sim_log.write('\n' + timestamp() + 'Finished merging files\n\n')

def simulation_dialogue():
    amount = []
    print("The following %d channels can be simulated:" % len(channels))
    for channel in channels:
        print(format_channel(channel))

    positive_response = ['y', 'Y', 'j', 'J', 'yes', 'Yes']
    negative_response = ['n', 'N', 'no', 'No']
    allowed_responses = list(positive_response)
    allowed_responses.extend(negative_response)
    a = input("\nShould be the same amount of events simulated for all channels? [y/n]: ")
    while a not in allowed_responses:
        a = input("You've entered an invalid response! Please try again: ")

    if a in positive_response:
        n_files = input_int("How much files per channel should be generated?")
        n_events = input_int("How much events should be stored in each file?")
        for channel in channels:
            max_number = check_simulation_files(channel)  # maximum file number of existing simulation files
            amount.append((channel, n_files, n_events, max_number))
    else:
        for channel in channels:
            n_files = input("How much files should be generated for channel "
                            + bold_string(format_channel(channel, False)) + " ?\n"
                            + " (just hit Enter if this channel should not be simulated) ")
            if not n_files or n_files == '0':
                print("Will not consider this channel.")
            else:
                try:
                    n_files = int(n_files)
                except:
                    print("Invalid input, will skip this channel!")
                    continue
                i = 0
                while True:
                    i += 1
                    try:
                        n_events = int(input("How much events should be stored in each file? "))
                        max_number = check_simulation_files(channel)  # maximum file number of existing simulation files
                        amount.append((channel, n_files, n_events, max_number))
                        break
                    except:
                        if i < 4:
                            print("Your input wasn't a number, please try again:")
                        else:
                            print("Invalid input, will skip this channel!")
                            break
    print()
    return amount

def process_config(config_file):
    amount = []
    print_color('Configuration file found, will read channels to be simulated from it\n', GREEN)
    lines = [line for line in config_file.readlines() if not line.startswith('#') and line.split()]  # last part excludes empty lines
    for line in lines:
        channel = line.split()
        try:
            if len(channel) != 3:
                print_error('[ERROR] Wrong number of arguments for channel %s' % channel[0])
                print('     This channel will be skipped')
            elif channel[0] not in channels:
                print_color('[WARNING] Channel "%s" unknown, will not be considered' % channel[0], RED)
            elif channel[1] is not '0' and channel[2] is not '0':
                max_number = check_simulation_files(channel[0])  # maximum file number of existing simulation files
                amount.append((channel[0], int(channel[1]), int(channel[2]), max_number))
            else:
                print('  Skip channel ' + format_channel(channel[0], False))
        except:
            print_error('[ERROR] Invalid syntax in the following line:\n%s' % line.rstrip())
            print('     This channel will be skipped')
    print()
    return amount


def main():
    # check command line arguments for channel configuration file
    channel_config = None
    list_files = False
    list_events = False
    if len(sys.argv) == 2:
        if sys.argv[1].startswith('--list'):
            if 'all' in sys.argv[1]:
                list_events = True
            else:
                list_files = True
        else:
            file = sys.argv[1]
            if not check_file('.', file):
                sys.exit(1)
            channel_config = open(file, 'r')
    elif len(sys.argv) > 2:
        print_error('[ERROR] Too many arguments')
        print('Usage: %s [%s]' % (sys.argv[0], 'config file'))
        print('Or to list the amount of existing files:')
        print('   %s --list' % sys.argv[0])
        sys.exit(1)

    # check if all needed paths and executables exist, terminate otherwise
    if not check_paths():
        sys.exit(1)

    # populate lists with existing simulation files
    global pluto_files, mkin_files, geant_files
    sim_files = os.listdir(pluto_data)
    geant_files = os.listdir(geant_data)
    mkin_files = [file for file in sim_files if '_mkin' in file]
    pluto_files = list(set(sim_files) - set(mkin_files))

    if list_files:
        list_file_amount()
        sys.exit(0)

    if list_events:
        list_file_amount(events=True)
        sys.exit(0)

    if RECONSTRUCT:
        print_color('NOTE: Reconstruction is enabled, GoAT files will be produced', BLUE)
        print_color('IMPORTANT: Please make sure you enabled a FinishMacro in your', YELLOW)
        print_color('           AcquRoot analysis config file which exits AcquRoot', YELLOW)
        print_color("           like the 'FinishMacro.C' provided within this repo", YELLOW)
        print()

    if SMEAR_Z_VERTEX:
        print_color('NOTE: Z vertex smearing is enabled. Z vertex position will be', BLUE)
        print_color('      smeared within a target length of %.2f cm' % Z_VERTEX_SMEARING, BLUE)
    if SMEAR_BEAM_POSITION:
        print_color('NOTE: Beam smearing is enabled. X and Y vertex position will be', BLUE)
        print_color('      smeared within a beam spot diameter of %.2f cm' % BEAM_SMEARING, BLUE)
    if SMEAR_Z_VERTEX or SMEAR_BEAM_POSITION:
        print()

    amount = []
    if not channel_config:
        amount = simulation_dialogue()
    else:
        amount = process_config(channel_config)
        channel_config.close()

    print(str(len(amount)) + " channels configured. The following simulation will take place:")
    total_files, total_events = 0, 0
    for channel, nf, ne, _ in amount:
        print("{0:<20s} {1:>3d} files per {2:>4s} events (total {3:>4s} events)"
                .format(format_channel(channel), nf, unit_prefix(ne), unit_prefix(nf*ne)))
        total_files += nf
        total_events += nf*ne
    print(" Total %s events in %d files" % (unit_prefix(total_events), total_files))
    print(" Files will be stored in " + DATA_OUTPUT_PATH)

    # simulation including reconstruction (new geant build) for 6M events done in around 72.9 hours --> ca. 12.15 hours per 1M events
    # pure reconstruction time for 1M events ca. 0.16 hours --> pure simulation time 11.99 hours
    if RECONSTRUCT:
        hours = round(total_events/1E6*12.15)
    else:
        hours = round(total_events/1E6*11.99)
    print("Pretty rough time estimation (based on a 3.2GHz Intel Dual-Core and 4GB RAM):")
    if hours > 24:
        print(" %d hours (about %d days and %d hours)" % (hours, hours/24, hours%24))
    elif hours == 0:
        print(" less than an hour")
    else:
        print(" %d hours" % hours)
    time_format = '%e. %B %Y %k:%M %Z'
    # add name of the day if simulation takes longer than 24 hours
    if hours > 24:
        time_format = '%A, ' + time_format
    # show finish time if simulation takes longer than 12 hours
    if hours > 12:
        print(' Finished approximately:  ' + (datetime.datetime.now() + datetime.timedelta(hours=hours)).strftime(time_format))

    input("\nStart the whole simulation process by hitting enter. ")

    # file which is used to save what is currently done
    global current_file
    current_file = get_path(DATA_OUTPUT_PATH, 'current_file')

    start_date = datetime.datetime.now()

    with open(get_path(DATA_OUTPUT_PATH, 'simulation.log'), 'w') as log:
        log.write(timestamp() + str(len(amount)) + " channels configured. The following simulation will take place:\n")
        for channel, nf, ne, _ in amount:
            log.write("{0:<20s} {1:>3d} files per {2:>4s} events (total {3:>4s} events)\n"
                    .format(format_channel(channel), nf, unit_prefix(ne), unit_prefix(nf*ne)))
        log.write(' Total %s events in %d files\n' % (unit_prefix(total_events), total_files))
        log.write(' Files will be stored in %s\n' % DATA_OUTPUT_PATH)
        log.flush()
        # do all the simulations
        pluto_simulation(amount, log)
        mkin_conversion(amount, log)
        geant_simulation(amount, log)
        if RECONSTRUCT:
            acqu(amount, log)
            goat(amount, log)
            hadd(amount, log)
        end_date = datetime.datetime.now()
        delta = end_date - start_date
        log.write('--- Finished after %.2f seconds ---' % delta.total_seconds())

    os.remove(current_file)

    time_format = time_format.replace('%k:%M', '%k:%M:%S')  # add seconds to the time format
    print('Simulation for %d channels done (total %s events)' % (len(amount), unit_prefix(total_events)))
    print('Start time: ' + start_date.strftime(time_format))
    print('Stop time:  ' + end_date.strftime(time_format))
    print('Elapsed:    %d s (%s)' % (round(delta.total_seconds()), str(delta).split('.')[0]))
    #print('Elapsed:    %d s (%d days, %d hours and %d minutes)' % (round(delta.total_seconds()), delta.days, delta.seconds/3600, delta.seconds%3600/60)
    print_color('\n - - - F I N I S H E D - - -\n', BLUE)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCtrl+C detected, will abort simulation process')
        sys.exit(0)
    except Exception as e:
        print('An error occured during execution:')
        print(e)
        sys.exit(1)
