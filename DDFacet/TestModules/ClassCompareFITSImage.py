import subprocess
import unittest
import os
from os import path, getenv

import numpy as np
from DDFacet.Parset.ReadCFG import Parset
from astropy.io import fits


class ClassCompareFITSImage(unittest.TestCase):
    """ Automated assurance test: reference FITS file regression (abstract class)
        Input:
            Accepts a set of reference images (defined in define_image_list),
            input measurement set and parset file.

            The parset file can be a subset of available
            options since DDFacet reads all values from the default parset. The
            overrides should specify an input measurement set or set of measurement
            sets.

            !!!Note: each measurement set should only be the name of the measurement
            !!!set since the tests must be portable. The names are automatically updated
            !!!to be relative to the data directory specified via environment variable
            !!!below.

            The parset should contain all the options that are to be tested in t
            he test case, but should not specify the output
            image file prefix, as this is overridden according to the filename
            rules below. Use setParsetOption to set a configuration option.

            Input filename convention:
                1. Input files directory: Set environment variable "DDFACET_TEST_DATA_DIR"
                                        (defaults to current directory)
                2. Reference image name: [TestClassName].[ImageIdentifier].fits
                3. Parset file: [TestClassName].parset.cfg

        Output filename convention:
            1. Output files directory: Set environment variable "DDFACET_TEST_OUTPUT_DIR"
                                        (defaults to tmp)
            2. Run-produced image name: [TestClassName].run.[ImageIdentifier].fits
            3. DDFacet logfiles: [TestClassName].run.out.log and [TestClassName].run.err.log
            4. Parset with default overrides, including image prefixes: [TestClassName].run.parset.conf
            5. Diff map as computed with fitstool.py with filename [TestClassName].diff.[ImageIdentifier].fits

        Tests cases:
            Tests the output of DDFacet against the reference images. Currently
            we are only testing the following:
                1. max (ref-output)^2 <= tolerance
                2. Mean Squared Error <= tolerance
    """

    @classmethod
    def defineImageList(cls):
        """ Method to define set of reference images to be tested.
            Can be overridden to add additional output products to the test.
            These must correspond to whatever is used in writing out the FITS files (eg. those in ClassDeconvMachine.py)
            Returns:
                List of image identifiers to reference and output products
        """
        return ['dirty', 'dirty.corr', 'psf', 'NormFacets', 'Norm',
                'int.residual', 'app.residual', 'int.model', 'app.model',
                'int.convmodel', 'app.convmodel', 'int.restored', 'app.restored',
                'restored']

    @classmethod
    def defineMaxSquaredError(cls):
        """ Method defining maximum error tolerance between any pair of corresponding
            pixels in the output and corresponding reference FITS images.
            Should be overridden if another tolerance is desired
            Returns:
                constant for maximum tolerance used in test case setup
        """
        return [1e-6,1e-6,1e-6,1e-6,1e-6,
                1e-3,1e-4,1e-3,1e-4,
                1e-3,1e-4,1e-3,1e-4,
                1e-1] #epsilons per image pair, as listed in defineImageList

    @classmethod
    def defMeanSquaredErrorLevel(cls):
	""" Method defining maximum tolerance for the mean squared error between any
	    pair of FITS images. Should be overridden if another tolerance is
	    desired
	    Returns:
		constant for tolerance on mean squared error
	"""
	return [1e-7,1e-7,1e-7,1e-7,1e-7,
                1e-5,1e-5,1e-5,1e-5,
                1e-5,1e-5,1e-5,1e-5,
                1e-5] #epsilons per image pair, as listed in defineImageList

    @classmethod
    def setParsetOption(cls, section, option, value):
        """
            Sets the default option read by the configuration parser
            args:
                section: Configuration [section] name
                option: Section option name
                value: Value for option (refer to default parset for documentation)
        """
        cls._defaultParsetConfig.set(section, option, value)

    @classmethod
    def setUpClass(cls):
        unittest.TestCase.setUpClass()
        cls._inputDir = getenv('DDFACET_TEST_DATA_DIR','./')+"/"
        cls._outputDir =  getenv('DDFACET_TEST_OUTPUT_DIR','/tmp/')+"/"
        cls._refHDUList = []
        cls._outHDUList = []

        #Read and override default parset
        cls._inputParsetFilename = cls._inputDir + cls.__name__+ ".parset.cfg"
        cls._outputParsetFilename = cls._outputDir + cls.__name__+ ".run.parset.cfg"
        if not path.isfile(cls._inputParsetFilename):
            raise RuntimeError("Default parset file %s does not exist" % cls._inputParsetFilename)
        p = Parset(File=cls._inputParsetFilename)
        cls._defaultParsetConfig = p.Config
        cls._imagePrefix = cls._outputDir+cls.__name__+".run"
        cls.setParsetOption("Images",
                            "ImageName",
                            cls._imagePrefix)
        # set up path to each ms relative to environment variable
        if type(p.DicoPars["VisData"]["MSName"]) is list:
            for ms in p.DicoPars["VisData"]["MSName"]:
                if path.dirname(ms) != "":
                    raise RuntimeError("Expected only measurement set name, "
                                       "not relative or absolute path in %s" % ms)
            abs_ms = [cls._inputDir+ms for ms in p.DicoPars["VisData"]["MSName"]]

            cls.setParsetOption("VisData", "MSName", "["+(",".join(abs_ms))+"]")
        else:
            ms = p.DicoPars["VisData"]["MSName"]
            if path.dirname(ms) != "":
                raise RuntimeError("Expected only measurement set name, "
                                    "not relative or absolute path in %s" % ms)
            abs_ms = cls._inputDir+ms
            cls.setParsetOption("VisData", "MSName", abs_ms)

        fOutputParset = open(cls._outputParsetFilename,mode='w')
        cls._defaultParsetConfig.write(fOutputParset)
        fOutputParset.close()

        #Build dictionary of HDUs
        for ref_id in cls.defineImageList():
            fname = cls._inputDir+cls.__name__+"."+ref_id+".fits"
            if not path.isfile(fname):
                raise RuntimeError("Reference image %s does not exist" % fname)
            fitsHDU = fits.open(fname)
            cls._refHDUList.append(fitsHDU)

        #Setup test constants
        cls._maxSqErr = cls.defineMaxSquaredError()
        cls._thresholdMSE = cls.defMeanSquaredErrorLevel()


        #Run DDFacet with desired setup. Crash the test if DDFacet gives a non-zero exit code:
        cls._stdoutLogFile = cls._outputDir+cls.__name__+".run.out.log"
        cls._stderrLogFile = cls._outputDir+cls.__name__+".run.err.log"

        args = ['DDF.py',
            cls._outputParsetFilename,
            '--ImageName=%s' % cls._imagePrefix]

        stdout_file = open(cls._stdoutLogFile, 'w')
        stderr_file = open(cls._stderrLogFile, 'w')

        with stdout_file, stderr_file:
            subprocess.check_call(args, env=os.environ.copy(),
                stdout=stdout_file, stderr=stderr_file)

        #Finally open up output FITS files for testing and build a dictionary of them
        for ref_id in cls.defineImageList():
            fname = cls._outputDir+cls.__name__+".run."+ref_id+".fits"
            if not path.isfile(fname):
                raise RuntimeError("Reference image %s does not exist" % fname)
            fitsHDU = fits.open(fname)
            cls._outHDUList.append(fitsHDU)

        #Save diffmaps for later use:
        for ref_id in cls.defineImageList():
            fname = cls._inputDir + cls.__name__ + "." + ref_id + ".fits"
            compfname = cls._outputDir + cls.__name__ + ".run." + ref_id + ".fits"
            difffname = cls._outputDir + cls.__name__ + ".diff." + ref_id + ".fits"
            args = ["fitstool.py", "-f", "--diff", "--output", difffname, fname, compfname]
            subprocess.check_call(args, env=os.environ.copy())

    @classmethod
    def tearDownClass(cls):
        unittest.TestCase.tearDownClass()
        for fitsfile in cls._refHDUList:
            fitsfile.close()
        for fitsfile in cls._outHDUList:
            fitsfile.close()

    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    '''
    Test cases:
    '''
    def testMaxSquaredError(self):
        cls = self.__class__
        list_except = []
        for imgI, (ref, out) in enumerate(zip(cls._refHDUList, cls._outHDUList)):
            imgIdentity = cls.defineImageList()[imgI] + " image"
            for ref_hdu, out_hdu in zip(ref, out):
                try:
                    if ref_hdu.data is None:
                        assert out_hdu.data is None, "ref_hdu data is None, so out_hdu must be None in %s" % imgIdentity
                    else:
                        assert out_hdu.data.shape == ref_hdu.data.shape, "ref_hdu data shape doesn't match out_hdu"
                    assert np.all((ref_hdu.data - out_hdu.data)**2 <= cls._maxSqErr[imgI]), "FITS data not the same for %s" % \
                                                                                            imgIdentity
                except AssertionError, e:
                    list_except.append(str(e))
                    continue
        if len(list_except) != 0:
            msg = "\n".join(list_except)
            raise AssertionError("The following assertions failed:\n %s" % msg)
    def testMeanSquaredError(self):
        cls = self.__class__
        list_except = []
        for imgI, (ref, out) in enumerate(zip(cls._refHDUList, cls._outHDUList)):
                imgIdentity = cls.defineImageList()[imgI] + " image"
                for ref_hdu, out_hdu in zip(ref, out):
                    try:
                        if ref_hdu.data is None:
                            assert out_hdu.data is None, "ref_hdu data is None, so out_hdu must be None in %s" % imgIdentity
                        else:
                            assert out_hdu.data.shape == ref_hdu.data.shape, "ref_hdu data shape doesn't match out_hdu"
                        assert np.mean((ref_hdu.data - out_hdu.data)**2) <= cls._thresholdMSE[imgI], "MSE of FITS data not the same for %s" % \
                                                             imgIdentity
                    except AssertionError, e:
                        list_except.append(str(e))
                    continue
        if len(list_except) != 0:
            msg = "\n".join(list_except)
            raise AssertionError("The following assertions failed:\n %s" % msg)

if __name__ == "__main__":
    pass # abstract class