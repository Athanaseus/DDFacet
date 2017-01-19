#!/usr/bin/env python
'''
DDFacet, a facet-based radio imaging package
Copyright (C) 2013-2016  Cyril Tasse, l'Observatoire de Paris,
SKA South Africa, Rhodes University

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''
#import matplotlib
# matplotlib.use('agg')
import optparse
import traceback
SaveFile = "last_DDFacet.obj"
import os, errno, re, sys, time, subprocess, psutil, numexpr
import numpy as np
from DDFacet.Other import logo
from DDFacet.Array import NpParallel
from DDFacet.Imager import ClassDeconvMachine
from DDFacet.Parset import ReadCFG
from DDFacet.Other import MyPickle
from DDFacet.Parset import MyOptParse
from DDFacet.Other import MyLogger
from DDFacet.Other import ModColor
from DDFacet.Other import ClassTimeIt
from DDFacet.Other import Multiprocessing
import SkyModel.Other.ModColor   # because it's duplicated there
from DDFacet.Other import progressbar
log = None


# # ##############################
# # Catch numpy warning
# np.seterr(all='raise')
# import warnings
# with warnings.catch_warnings():
#     warnings.filterwarnings('error')
# # ##############################

'''
The defaults for all the user commandline arguments are stored in a parset configuration file
called DefaultParset.cfg. When you add a new option you must specify meaningful defaults in
there.

These options can be overridden by specifying a subset of the parset options in a user parset file
passed as the first commandline argument. These options will override the corresponding defaults.
'''
import DDFacet
print "Using python package located at: " + os.path.dirname(DDFacet.__file__)
print "Using driver file located at: " + __file__
global Parset
Parset = ReadCFG.Parset("%s/DefaultParset.cfg" % os.path.dirname(DDFacet.Parset.__file__))


def read_options():

    default_values = Parset.value_dict
    attrs = Parset.attr_dict

    desc = """Questions and suggestions: cyril.tasse@obspm.fr"""

    OP = MyOptParse.MyOptParse(usage='Usage: %prog [parset file] <options>', version='%prog version 1.0',
                               description=desc, defaults=default_values, attributes=attrs)

    # create options based on contents of parset
    for section in Parset.sections:
        values = default_values[section]
        # "_Help" value in each section is its documentation string
        OP.OptionGroup(values.get("_Help", section), section)
        for name, value in default_values[section].iteritems():
            if not attrs[section][name].get("no_cmdline"):
                OP.add_option(name, value)

    OP.Finalise()
    OP.ReadInput()

    # #optcomplete.autocomplete(opt)

    # options, arguments = opt.parse_args()
    MyPickle.Save(OP, SaveFile)
    return OP


def test():
    options = read_options()


def main(OP=None, messages=[]):
    if OP is None:
        OP = MyPickle.Load(SaveFile)

    DicoConfig = OP.DicoConfig

    ImageName = DicoConfig["Output"]["Name"]
    if not ImageName:
        raise ValueError("--Output-Name not specified")

    # create directory if it exists
    dirname = os.path.dirname(ImageName)
    if not os.path.exists(dirname) and not dirname == "":
        os.mkdir(dirname)

    # setup logging
    MyLogger.logToFile(ImageName + ".log", append=DicoConfig["Log"]["Append"])
    global log
    log = MyLogger.getLogger("DDFacet")

    # disable colors and progressbars if requested
    ModColor.silent = SkyModel.Other.ModColor.silent = \
                      progressbar.ProgressBar.silent = \
                      DicoConfig["Log"]["Boring"]

    if messages:
        if not DicoConfig["Log"]["Boring"]:
            os.system('clear')
            logo.print_logo()
        for msg in messages:
            print>> log, msg

    # print current options
    OP.Print(dest=log)

    # enable memory logging
    MyLogger.enableMemoryLogging(DicoConfig["Log"]["Memory"])

    # get rid of old shm arrays from previous runs
    Multiprocessing.cleanupStaleShm()

    # initialize random seed from config if set, or else from system time
    if DicoConfig["Misc"]["RandomSeed"] is not None:
        print>>log, "random seed=%d (explicit)" % DicoConfig["Misc"]["RandomSeed"]
    else:
        DicoConfig["Misc"]["RandomSeed"] = int(time.time())
        print>> log, "random seed=%d (automatic)" % DicoConfig["Misc"]["RandomSeed"]
    np.random.seed(DicoConfig["Misc"]["RandomSeed"])

    # If we're using Montblanc for the Predict, we need to use a remote
    # tensorflow server as tensorflow is not fork safe
    # http://stackoverflow.com/questions/37874838/forking-a-python-process-after-loading-tensorflow
    # If a TensorFlowServerTarget is not specified, fork a child process containing one.
    if DicoConfig["Image"]["PredictMode"] == "Montblanc":
        if not DicoConfig["Montblanc"]["TensorflowServerTarget"]:
            from DDFacet.TensorFlowServerFork import fork_tensorflow_server
            DicoConfig["Montblanc"]["TensorflowServerTarget"] = fork_tensorflow_server()

    # init NCPU for different bits of parallelism
    ncpu = DicoConfig["Parallel"]["NCPU"] or psutil.cpu_count()
    NpParallel.NCPU_global = ncpu
    numexpr.set_num_threads(ncpu)
    print>>log,"using up to %d CPUs for parallelism" % ncpu

    # write parset
    OP.ToParset("%s.parset"%ImageName)

    Mode = DicoConfig["Image"]["Mode"]

    # data machine initialized for all cases except PSF-only mode
    # psf machine initialized for all cases except Predict-only mode
    Imager = ClassDeconvMachine.ClassImagerDeconv(GD=DicoConfig, IdSharedMem=Multiprocessing.getShmPrefix(), BaseName=ImageName,
                                                  data=(Mode != "PSF"), psf=(Mode != "Predict"),
                                                  deconvolve=("Clean" in Mode))

    Imager.Init()

    # Imager.testDegrid()
    # stop
    if "Predict" in Mode:
        Imager.GivePredict()
    if "Clean" in Mode:
        Imager.main()
    elif "Dirty" in Mode:
        sparsify = DicoConfig["Comp"]["Sparsification"]
        if sparsify and isinstance(sparsify, list):
            sparsify = sparsify[0]
        Imager.GiveDirty(psf="PSF" in Mode, sparsify=sparsify)
    elif "PSF" in Mode:
        sparsify = DicoConfig["Comp"]["Sparsification"]
        if sparsify and isinstance(sparsify, list):
            sparsify = sparsify[0]
        Imager.MakePSF(sparsify=sparsify)

    # # open default viewer, these options should match those in
    # # ClassDeconvMachine if changed:
    # viewer = DicoConfig["Output"]["DefaultImageViewer"]
    # for img in DicoConfig["Output"]["Open"]:
    #     if img == "Dirty":
    #         ret = subprocess.call(
    #             "%s %s.dirty.fits" %
    #             (viewer, DicoConfig["Output"]["Name"]),
    #             shell=True)
    #         if ret:
    #             print>>log, ModColor.Str(
    #                 "\nCan't open dirty image\n", col="yellow")
    #     elif img == "DirtyCorr":
    #         ret = subprocess.call(
    #             "%s %s.dirty.corr.fits" %
    #             (viewer, DicoConfig["Output"]["Name"]),
    #             shell=True)
    #         if ret:
    #             print>>log, ModColor.Str(
    #                 "\nCan't open dirtyCorr image\n", col="yellow")
    #     elif img == "PSF":
    #         ret = subprocess.call(
    #             "%s %s.psf.fits" %
    #             (viewer, DicoConfig["Output"]["Name"]), shell=True)
    #         if ret:
    #             print>>log, ModColor.Str(
    #                 "\nCan't open PSF image\n", col="yellow")
    #     elif img == "Model":
    #         ret = subprocess.call(
    #             "%s %s.model.fits" %
    #             (viewer, DicoConfig["Output"]["Name"]),
    #             shell=True)
    #         if ret:
    #             print>>log, ModColor.Str(
    #                 "\nCan't open model image\n", col="yellow")
    #     elif img == "Residual":
    #         ret = subprocess.call(
    #             "%s %s.residual.fits" %
    #             (viewer, DicoConfig["Output"]["Name"]),
    #             shell=True)
    #         if ret:
    #             print>>log, ModColor.Str(
    #                 "\nCan't open residual image\n", col="yellow")
    #     elif img == "Restored":
    #         ret = subprocess.call(
    #             "%s %s.restored.fits" %
    #             (viewer, DicoConfig["Output"]["Name"]),
    #             shell=True)
    #         if ret:
    #             print>>log, ModColor.Str(
    #                 "\nCan't open restored image\n", col="yellow")
    #     elif img == "Alpha":
    #         ret = subprocess.call(
    #             "%s %s.alpha.fits" %
    #             (viewer, DicoConfig["Output"]["Name"]),
    #             shell=True)
    #         if ret:
    #             print>>log, ModColor.Str(
    #                 "\nCan't open alpha image\n", col="yellow")
    #     elif img == "Norm":
    #         ret = subprocess.call(
    #             "%s %s.Norm.fits" %
    #             (viewer, DicoConfig["Output"]["Name"]),
    #             shell=True)
    #         if ret:
    #             print>>log, ModColor.Str(
    #                 "\nCan't open norm image\n", col="yellow")
    #     elif img == "NormFacets":
    #         ret = subprocess.call(
    #             "%s %s.NormFacets.fits" %
    #             (viewer, DicoConfig["Output"]["Name"]),
    #             shell=True)
    #         if ret:
    #             print>>log, ModColor.Str(
    #                 "\nCan't open normfacets image\n", col="yellow")
    #     else:
    #         print>>log, ModColor.Str(
    #             "\nDon't understand %s, not opening that image\n" %
    #             img, col="yellow")
    Multiprocessing.cleanupShm()

if __name__ == "__main__":
    #os.system('clear')
    logo.print_logo()
    T = ClassTimeIt.ClassTimeIt()

    # parset should have been read in by now
    OP = read_options()
    args = OP.GiveArguments()

    # collect messages in a list here because I don't want to log them until the logging system
    # is set up in main()
    messages = ["starting DDFacet (%s)" % " ".join(sys.argv),
                "working directory is %s" % os.getcwd()]

    # single argument is a parset to read
    if len(args) == 1:
        ParsetFile = args[0]
        TestParset = ReadCFG.Parset(ParsetFile)
        if TestParset.success:
            Parset.update_values(TestParset, newval=False)
            if TestParset.migrated is not None:
                messages.append(ModColor.Str("WARNING: parset %s is of a deprecated version %.1f"%(ParsetFile, TestParset.migrated)))
                messages.append(ModColor.Str("We have migrated the parset to the current version (%.1f) automatically,"%(TestParset.version)))
                messages.append(ModColor.Str("but please check the settings below to make sure they're correct."))
            else:
                messages.append("Successfully read parset %s, version %.1f"%(ParsetFile, TestParset.version))
        else:
            OP.ExitWithError(
                "Argument must be a valid parset file. Use -h for help.")
            sys.exit(1)
        # re-read options, since defaults will have been updated by the parset
        OP = read_options()
        # refuse to clobber existing parsets, unless forced from command line
        new_parset = OP.DicoConfig["Output"]["Name"] + ".parset"
        if os.path.exists(new_parset) and os.path.samefile(ParsetFile, new_parset):
            if OP.DicoConfig["Output"]["Clobber"]:
                print>> log, ModColor.Str("WARNING: will overwrite existing parset, since --Clobber is specified.")
            else:
                print>> log, ModColor.Str("Your --Output-Name setting is the same as the base name of the parset, which would\n"
                                          "mean overwriting the parset. I'm sorry, Dave, I'm afraid I can't do that.\n"
                                          "Please re-run with the --Output-Clobber option if you're sure this is what\n"
                                          "you want to do, or set a different --Output-Name.")
                sys.exit(1)
    elif len(args):
        OP.ExitWithError("Incorrect number of arguments. Use -h for help.")
        sys.exit(1)

    retcode = 0
    try:
        main(OP, messages)
        print>>log, ModColor.Str(
            "DDFacet ended successfully after %s" %
            T.timehms(), col="green")
    except KeyboardInterrupt:
        print>>log, traceback.format_exc()
        print>>log, ModColor.Str("DDFacet interrupted by Ctrl+C", col="red")
        retcode = 1 #Should at least give the command line an indication of failure
    except:
        print>>log, traceback.format_exc()
        ddfacetPath = "." if os.path.dirname(
            __file__) == "" else os.path.dirname(__file__)
        traceback_msg = traceback.format_exc()
        try:
            commitSha = subprocess.check_output(
                "git -C %s rev-parse HEAD" %
                ddfacetPath, shell=True)
        except subprocess.CalledProcessError:
            import DDFacet.version as version
            commitSha = version.__version__

        logfileName = MyLogger.getLogFilename()
        logfileName = logfileName if logfileName is not None else "[file logging is not enabled]"
        print>> log, ModColor.Str(
            "There was a problem after %s, if you think this is a bug please open an "
            "issue, quote your version of DDFacet and attach your logfile" %
            T.timehms(), col="red")
        print>> log, ModColor.Str(
            "You are using DDFacet revision: %s" %
            commitSha, col="red")
        print>> log, ModColor.Str(
            "Your logfile is available here: %s" %
            logfileName, col="red")
        print>>log, traceback_msg
        # Should at least give the command line an indication of failure
        retcode = 1 # Should at least give the command line an indication of failure

    Multiprocessing.cleanupShm()
    sys.exit(retcode)
