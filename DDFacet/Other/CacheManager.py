import os
import os.path
import cPickle

from DDFacet.Other import MyLogger
log = MyLogger.getLogger("CacheManager")


class CacheManager (object):
    """
    # CacheManager

    This is a simple disk-based cache management class. Usage is as follows:

        cache = CacheManager("/cache/directory")

    This creates a cache based on the specified path. Directory is created if it doesn't exist.
    If you create CacheManager with reset=True, the contents of the directory are deleted.

    Typically, you would use the cache in the following pattern:

        path, valid = cache.checkCache("foo", hashvalue)
        if valid:
            ## your data is on disk and good, load it from "path". E.g.
            data = numpy.load(path)
        else:
            ## your data must be recomputed. Recompute it and save it to "path".
            data = expensiveComputation()
            numpy.save(path, data)
            cache.saveCache("foo")  # mark the cache as valid

    So: checkCache() returns a path to the item (/cache/directory/foo, in this case), and a flag telling
    you if the saved item is valid. The item is considered valid if /cache/directory/foo exists, **and**
    /cache/directory/foo.hash exists, **and** contains the same value as the supplied "hashvalue". Thus,
    if hashvalue has changed w.r.t. the stored hash, then the cache is invalid.

    Hashvalue may be any Python object supporting the comparison operator (for example, a dict).
    Typically, this would be a dict of parameters any changes in which should cause the data item
    to be recomputed.

    The saveCache("foo") call is vitally important! The cache manager cannot know by itself when
    you've successfully written to the cache. By calling saveCache(), you're telling it that your data
    has been safely written to /cache/directory/foo. The cache manager then takes the hashvalue you
    supplied in the previous checkCache() call, and saves it to /cache/directory/foo.hash.


    # Using cache manager in DDFacet

    DDFacet caches the following data items:

        * W-kernels & other facet-related data

        * BDA mappings for gridding and degridding, flags, Jones matrices

    Each MS has a top-level cache named mspath.ddfcache, and per-chunk caches named
    mspath.ddfcache/Fx:Dy:n:m, where F is field ID, D is DDID, and n:m are row numbers.
    The per-chunk caches are used when iterating over MSs during gridding/degridding.

    Each ClassMS object has an ms.maincache attribute, and an ms.cache attribute.
    The former corresponds to that MS's top-level cache. The latter corresponds to
    the cache of the current chunk being iterated over.

    The ClassVisServer object has a VS.maincache an a VS.cache attribute. VS.maincache
    points to the maincache of the first MS in the list. This is used to cache facet data.
    VS.cache points to the cache of the current chunk of the current MS being iterated over.
    This is used to cache the various mappings.

    To form up hashvalues, the global dict (GD) object is very convenient. Sections of GD
    that influence a particular cache item are used as the hashvalue in each case.

    Running with DeleteDDFProducts=1 causes all caches to be reset.
    """

    def __init__(self, dirname, reset=False):
        """
        Initializes cache manager.

        Args:
            dirname: directory in which caches are kept
            reset: if True, cache is reset upon first access
        """
        self.dirname = dirname
        self.hashes = {}
        self.pid = os.getpid()
        if not os.path.exists(dirname):
            print>>log, ("cache directory %s does not exist, creating" % dirname)
            os.mkdir(dirname)
        else:
            if reset:
                print>> log, ("clearing cache %s, since we were asked to reset the cache" % dirname)
                os.system("rm -fr "+dirname)
                os.mkdir(dirname)

    @staticmethod
    def getElementName (name, **kw):
        """Helper function. Forms up a cache element filename as "NAME:KEY1_VALUE1:KEY2_VALUE2..."
        For example: getElementName("WTerm",facet=1)

        Args:
            name: name of cache element
            **kw: optional keywords, will be added to name as ":key_value"

        Returns:
            Concatenated Filename
        """
        return ":".join([name] + [ "%s_%s"%(key, value) for key, value in sorted(kw.items()) ])

    def getElementPath(self, name, **kw):
        """
        Forms up a full path for cache element 'name', with extra keywords. This is the element name plus
        the cache path. See getElementName() for usage.
        """
        return os.path.join(self.dirname, self.getElementName(name, **kw))

    def getShmName (self, name, **kw):
        """
        Forms up a name for a shm-backed shared element. This takes the form of "ddf.PID.", where PID is the
        pid of the process where the cache manager was created (so the parent process, presumably), followed
        by a filename of the form "NAME:KEY1_VALUE1:...", as returned by getElementName(). See getElementName()
        for usage.
        """
        return "ddf.%d.%s" % (os.getpid(), self.getElementName(name, **kw))

    def getShmURL (self, name, **kw):
        """
        Forms up a URL for a shm-backed shared element. This takes the form of "shm://" plus getShmName()
        """
        return "shm://" + self.getShmName(name, **kw)

    def getCacheURL (self, name, **kw):
        """
        Forms up a URL for a disk-backed shared element. This takes the form of "file://PATH", where path is
        the cache element path as formed by getElementPath(). See the latter for usage.
        """
        return "file://" + self.getElementPath(name, **kw)

    def getURL(self, name, disk=False, **kw):
        """
        Forms up a URL for a disk- or shm-backed shared element. For disk=False, calls getShmURL(). For disk=True,
        calls getCacheURL()
        """
        return self.getCacheURL(name, **kw) if disk else self.getShmURL(name, **kw)


    def checkCache(self, name, hashkeys, directory=False, reset=False):
        """
        Checks if cached element named "name" is valid.

        Args:
            name: name of cache element
            hashkeys: dictionary of keys upon which the cached object depends. If a hash of the keys does not
                match the stored hash value, the cache is invalid and will be reset.
            directory: if True, cache is a directory and not a file. The directory will be created if it
                doesn't exist. If the cache is invalid, the contents of the directory will be deleted.
            reset: if True, cache item is deleted

        Returns:
            tuple of (path, valid)
            where path is a path to cache object (or cache directory)
            and valid is True if a valid cache exists
        """
        cachepath = self.getElementPath(name)
        hashpath = cachepath + ".hash"
        # convert hash keys into a single list
        hash = hashkeys
        self.hashes[name] = hashpath, hash
        # delete cache if explicitly asked to
        if reset:
            print>>log, "cache element %s will be explicitly reset" % cachepath
        else:
            if not os.path.exists(cachepath):
                print>>log, "cache element %s does not exist, will re-make" % cachepath
                if directory:
                    os.mkdir(cachepath)
                reset = True
            # check for stored hash
            if not reset:
                try:
                    storedhash = cPickle.load(file(hashpath))
                except:
                    print>>log, "cache hash %s invalid, will re-make" % hashpath
                    reset = True
            # check for hash match
            if not reset and hash != storedhash:
                print>>log, "cache hash %s does not match, will re-make" % hashpath
                reset = True
            # if resetting cache, then mark new hash value for saving (will be saved in flushCache),
            # and remove any existing cache/hash
        if reset:
            if os.path.exists(hashpath):
                os.unlink(hashpath)
            if os.path.exists(cachepath):
                if directory:
                    if os.system("rm -fr %s" % cachepath):
                        raise OSError,"Failed to remove cache directory %s. Check permissions/ownership." % cachepath
                    os.mkdir(cachepath)
                else:
                    os.unlink(cachepath)
        # store hash
        self.hashes[name] = hashpath, hash, reset
        return cachepath, not reset

    def saveCache(self, name=None):
        """
        Saves cache hash to disk. Meant to be called after a cache object has been successfully written to.

        Args:
            name: name of cache object. If None, all accumulated objects are flushed.

        Returns:

        """
        names = [name] if name else self.hashes.keys()
        for name in names:
            hashpath, hash, reset = self.hashes[name]
            if reset:
                cPickle.dump(hash, file(hashpath, "w"))
                print>>log, "writing cache hash %s" % hashpath
                del self.hashes[name]
