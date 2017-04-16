#!/usr/bin/env python
# encoding: utf-8

"""Start the IPython Engine."""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

# Python looks for an empty string at the beginning of sys.path to enable
# importing from the cwd.
import sys
sys.path.insert(0, '')

from optparse import OptionParser
import os

from twisted.application import service
from twisted.internet import reactor
from twisted.python import log

from IPython.kernel.fcutil import Tub, UnauthenticatedTub

from IPython.kernel.core.config import config_manager as core_config_manager
from IPython.config.cutils import import_item
from IPython.kernel.engineservice import EngineService

# Create various ipython directories if they don't exist.
# This must be done before IPython.kernel.config is imported.
from IPython.iplib import user_setup
from IPython.genutils import get_ipython_dir, get_log_dir, get_security_dir
if os.name == 'posix':
    rc_suffix = ''
else:
    rc_suffix = '.ini'
user_setup(get_ipython_dir(), rc_suffix, mode='install', interactive=False)
get_log_dir()
get_security_dir()

from IPython.kernel.config import config_manager as kernel_config_manager
from IPython.kernel.engineconnector import EngineConnector


#-------------------------------------------------------------------------------
# Code
#-------------------------------------------------------------------------------

def start_engine():
    """
    Start the engine, by creating it and starting the Twisted reactor.
    
    This method does:
    
        * If it exists, runs the `mpi_import_statement` to call `MPI_Init`
        * Starts the engine logging
        * Creates an IPython shell and wraps it in an `EngineService`
        * Creates a `foolscap.Tub` to use in connecting to a controller.
        * Uses the tub and the `EngineService` along with a Foolscap URL
          (or FURL) to connect to the controller and register the engine
          with the controller
    """
    kernel_config = kernel_config_manager.get_config_obj()
    core_config = core_config_manager.get_config_obj()
    

    # Execute the mpi import statement that needs to call MPI_Init
    global mpi
    mpikey = kernel_config['mpi']['default']
    mpi_import_statement = kernel_config['mpi'].get(mpikey, None)
    if mpi_import_statement is not None:
        try:
            exec mpi_import_statement in globals()
        except:
            mpi = None
    else:
        mpi = None
    
    # Start logging
    logfile = kernel_config['engine']['logfile']
    if logfile:
        logfile = logfile + str(os.getpid()) + '.log'
        try:
            openLogFile = open(logfile, 'w')
        except:
            openLogFile = sys.stdout
    else:
        openLogFile = sys.stdout
    log.startLogging(openLogFile)
    
    # Create the underlying shell class and EngineService
    shell_class = import_item(core_config['shell']['shell_class'])
    engine_service = EngineService(shell_class, mpi=mpi)
    shell_import_statement = core_config['shell']['import_statement']
    if shell_import_statement:
        try:
            engine_service.execute(shell_import_statement)
        except:
            log.msg("Error running import_statement: %s" % shell_import_statement)
    
    # Create the service hierarchy
    main_service = service.MultiService()
    engine_service.setServiceParent(main_service)
    tub_service = Tub()
    tub_service.setServiceParent(main_service)
    # This needs to be called before the connection is initiated
    main_service.startService()
    
    # This initiates the connection to the controller and calls
    # register_engine to tell the controller we are ready to do work
    engine_connector = EngineConnector(tub_service)
    furl_file = kernel_config['engine']['furl_file']
    log.msg("Using furl file: %s" % furl_file)
    
    def call_connect(engine_service, furl_file):
        d = engine_connector.connect_to_controller(engine_service, furl_file)
        def handle_error(f):
            # If this print statement is replaced by a log.err(f) I get
            # an unhandled error, which makes no sense.  I shouldn't have
            # to use a print statement here.  My only thought is that
            # at the beginning of the process the logging is still starting up
            print "error connecting to controller:", f.getErrorMessage()
            reactor.callLater(0.1, reactor.stop)
        d.addErrback(handle_error)
    
    reactor.callWhenRunning(call_connect, engine_service, furl_file)
    reactor.run()


def init_config():
    """
    Initialize the configuration using default and command line options.
    """
    
    parser = OptionParser("""ipengine [options]

Start an IPython engine.

Use the IPYTHONDIR environment variable to change your IPython directory 
from the default of .ipython or _ipython.  The log and security 
subdirectories of your IPython directory will be used by this script 
for log files and security files.""")
    
    parser.add_option(
        "--furl-file",
        type="string", 
        dest="furl_file",
        help="The filename containing the FURL of the controller"
    )
    parser.add_option(
        "--mpi",
        type="string",
        dest="mpi",
        help="How to enable MPI (mpi4py, pytrilinos, or empty string to disable)"
    )
    parser.add_option(
        "-l",
        "--logfile",
        type="string",
        dest="logfile",
        help="log file name (default is stdout)"
    )
    
    (options, args) = parser.parse_args()
    
    kernel_config = kernel_config_manager.get_config_obj()
    # Now override with command line options
    if options.furl_file is not None:
        kernel_config['engine']['furl_file'] = options.furl_file
    if options.logfile is not None:
        kernel_config['engine']['logfile'] = options.logfile
    if options.mpi is not None:
        kernel_config['mpi']['default'] = options.mpi


def main():
    """
    After creating the configuration information, start the engine.
    """
    init_config()
    start_engine()


if __name__ == "__main__":
    main()
