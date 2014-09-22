"""
The matplotlib build options can be modified with a setup.cfg file. See
setup.cfg.template for more information.
"""

from __future__ import print_function, absolute_import

# This needs to be the very first thing to use distribute
from distribute_setup import use_setuptools
use_setuptools()

import sys

# distutils is breaking our sdists for files in symlinked dirs.
# distutils will copy if os.link is not available, so this is a hack
# to force copying
import os
try:
    del os.link
except AttributeError:
    pass

# This 'if' statement is needed to prevent spawning infinite processes
# on Windows
if __name__ == '__main__':
    # BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
    # update it when the contents of directories change.
    if os.path.exists('MANIFEST'):
        os.remove('MANIFEST')

try:
    from setuptools import setup
except ImportError:
    try:
        from setuptools.core import setup
    except ImportError:
        from distutils.core import setup

# The setuptools version of sdist adds a setup.cfg file to the tree.
# We don't want that, so we simply remove it, and it will fall back to
# vanilla distutils.
try:
    from setuptools.command import sdist
except ImportError:
    pass
else:
    del sdist.sdist.make_release_tree

from distutils.dist import Distribution

import setupext
from distutils.command.build_ext import build_ext
from setupext import print_line, print_raw, print_message, print_status

# Get the version from the source code
__version__ = setupext.Matplotlib().check()


class build_ext_subclass(build_ext):
    """
    This fixes a problem with building packages when environmental variable
    CXX consists of compiler name + arguments with spaces in the middle.
    build_ext instead expects an array where each element is a CLI token, and
    so normally compilation would fail with error "unable to execute
    `cxx[0]`: No such file or directory. This subclass of build_ext extracts
    the compiler name and places remaining arguments back into the array
    """
    def build_extensions(self):
        ccm = self.compiler.compiler
        if ' ' in ccm:
            self.compiler.compiler = ccm[0].split(' ') + ccm[1:]
        cxx = self.compiler.compiler_cxx
        if ' ' in cxx[0]:
            self.compiler.compiler_cxx = cxx[0].split(' ') + cxx[1:]
        build_ext.build_extensions(self)


# These are the packages in the order we want to display them.  This
# list may contain strings to create section headers for the display.
mpl_packages = [
    'Building Matplotlib',
    setupext.Matplotlib(),
    setupext.Python(),
    setupext.Platform(),
    'Required dependencies and extensions',
    setupext.Numpy(),
    setupext.Six(),
    setupext.Dateutil(),
    setupext.Tornado(),
    setupext.Pyparsing(),
    setupext.CXX(),
    setupext.LibAgg(),
    setupext.FreeType(),
    setupext.FT2Font(),
    setupext.Png(),
    setupext.Qhull(),
    setupext.Image(),
    setupext.TTConv(),
    setupext.Path(),
    setupext.Contour(),
    setupext.Delaunay(),
    setupext.QhullWrap(),
    setupext.Tri(),
    'Optional subpackages',
    setupext.SampleData(),
    setupext.Toolkits(),
    setupext.Tests(),
    setupext.Toolkits_Tests(),
    'Optional backend extensions',
    # These backends are listed in order of preference, the first
    # being the most preferred.  The first one that looks like it will
    # work will be selected as the default backend.
    setupext.BackendMacOSX(),
    setupext.BackendQt5(),
    setupext.BackendQt4(),
    setupext.BackendPySide(),
    setupext.BackendGtk3Agg(),
    setupext.BackendGtk3Cairo(),
    setupext.BackendGtkAgg(),
    setupext.BackendTkAgg(),
    setupext.BackendWxAgg(),
    setupext.BackendGtk(),
    setupext.BackendAgg(),
    setupext.BackendCairo(),
    setupext.Windowing(),
    'Optional LaTeX dependencies',
    setupext.DviPng(),
    setupext.Ghostscript(),
    setupext.LaTeX(),
    setupext.PdfToPs()
    ]


classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: Python Software Foundation License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 3',
    'Topic :: Scientific/Engineering :: Visualization',
    ]

# One doesn't normally see `if __name__ == '__main__'` blocks in a setup.py,
# however, this is needed on Windows to avoid creating infinite subprocesses
# when using multiprocessing.
if __name__ == '__main__':
    # These are distutils.setup parameters that the various packages add
    # things to.
    packages = []
    namespace_packages = []
    py_modules = []
    ext_modules = []
    package_data = {}
    package_dir = {'': 'lib'}
    install_requires = []
    setup_requires = []
    default_backend = None

    # Go through all of the packages and figure out which ones we are
    # going to build/install.
    print_line()
    print_raw("Edit setup.cfg to change the build options")

    required_failed = []
    good_packages = []
    for package in mpl_packages:
        if isinstance(package, str):
            print_raw('')
            print_raw(package.upper())
        else:
            try:
                result = package.check()
                if result is not None:
                    message = 'yes [%s]' % result
                    print_status(package.name, message)
            except setupext.CheckFailed as e:
                msg = str(e).strip()
                if len(msg):
                    print_status(package.name, 'no  [%s]' % msg)
                else:
                    print_status(package.name, 'no')
                if not package.optional:
                    required_failed.append(package)
            else:
                good_packages.append(package)
                if isinstance(package, setupext.OptionalBackendPackage):
                    if default_backend is None:
                        default_backend = package.name
    print_raw('')

    # Abort if any of the required packages can not be built.
    if required_failed:
        print_line()
        print_message(
            "The following required packages can not "
            "be built: %s" %
            ', '.join(x.name for x in required_failed))
        sys.exit(1)

    # Now collect all of the information we need to build all of the
    # packages.
    for package in good_packages:
        if isinstance(package, str):
            continue
        packages.extend(package.get_packages())
        namespace_packages.extend(package.get_namespace_packages())
        py_modules.extend(package.get_py_modules())
        ext = package.get_extension()
        if ext is not None:
            ext_modules.append(ext)
        data = package.get_package_data()
        for key, val in data.items():
            package_data.setdefault(key, [])
            package_data[key] = list(set(val + package_data[key]))
        install_requires.extend(package.get_install_requires())
        setup_requires.extend(package.get_setup_requires())

    # Write the default matplotlibrc file
    if default_backend is None:
        default_backend = 'svg'
    if setupext.options['backend']:
        default_backend = setupext.options['backend']
    with open('matplotlibrc.template') as fd:
        template = fd.read()
    with open('lib/matplotlib/mpl-data/matplotlibrc', 'w') as fd:
        fd.write(template % {'backend': default_backend})

    # Build in verbose mode if requested
    if setupext.options['verbose']:
        for mod in ext_modules:
            mod.extra_compile_args.append('-DVERBOSE')

    # Finalize the extension modules so they can get the Numpy include
    # dirs
    for mod in ext_modules:
        mod.finalize()

    extra_args = {}

    # Avoid installing setup_requires dependencies if the user just
    # queries for information
    if (any('--' + opt in sys.argv for opt in
            Distribution.display_option_names + ['help']) or
            'clean' in sys.argv):
        setup_requires = []

    # Finally, pass this all along to distutils to do the heavy lifting.
    distrib = setup(
        name="matplotlib",
        version=__version__,
        description="Python plotting package",
        author="John D. Hunter, Michael Droettboom",
        author_email="mdroe@stsci.edu",
        url="http://matplotlib.org",
        long_description="""
        matplotlib strives to produce publication quality 2D graphics
        for interactive graphing, scientific publishing, user interface
        development and web application servers targeting multiple user
        interfaces and hardcopy output formats.  There is a 'pylab' mode
        which emulates matlab graphics.
        """,
        license="BSD",
        packages=packages,
        namespace_packages=namespace_packages,
        platforms='any',
        py_modules=py_modules,
        cmdclass={'build_ext': build_ext_subclass},
        ext_modules=ext_modules,
        package_dir=package_dir,
        package_data=package_data,
        classifiers=classifiers,
        download_url="https://downloads.sourceforge.net/project/matplotlib/matplotlib/matplotlib-{0}/matplotlib-{0}.tar.gz".format(__version__),

        # List third-party Python packages that we require
        install_requires=install_requires,
        setup_requires=setup_requires,

        # matplotlib has C/C++ extensions, so it's not zip safe.
        # Telling setuptools this prevents it from doing an automatic
        # check for zip safety.
        zip_safe=False,

        **extra_args
    )
