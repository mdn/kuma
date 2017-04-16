#!/usr/bin/env python
# encoding: utf-8

"""The IPython controller."""

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
import time
import tempfile

from twisted.application import internet, service
from twisted.internet import reactor, error, defer
from twisted.python import log

from IPython.kernel.fcutil import Tub, UnauthenticatedTub, have_crypto

# from IPython.tools import growl
# growl.start("IPython1 Controller")

from IPython.kernel.error import SecurityError
from IPython.kernel import controllerservice
from IPython.kernel.fcutil import check_furl_file_security

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
from IPython.config.cutils import import_item


#-------------------------------------------------------------------------------
# Code
#-------------------------------------------------------------------------------

def get_temp_furlfile(filename):
    return tempfile.mktemp(dir=os.path.dirname(filename),
                           prefix=os.path.basename(filename))

def make_tub(ip, port, secure, cert_file):
    """
    Create a listening tub given an ip, port, and cert_file location.
    
    :Parameters:
        ip : str
            The ip address that the tub should listen on.  Empty means all
        port : int
            The port that the tub should listen on.  A value of 0 means
            pick a random port
        secure: boolean
            Will the connection be secure (in the foolscap sense)
        cert_file:
            A filename of a file to be used for theSSL certificate
    """
    if secure:
        if have_crypto:
            tub = Tub(certFile=cert_file)
        else:
            raise SecurityError("""
OpenSSL/pyOpenSSL is not available, so we can't run in secure mode.
Try running without security using 'ipcontroller -xy'.
""")
    else:
        tub = UnauthenticatedTub()
    
    # Set the strport based on the ip and port and start listening
    if ip == '':
        strport = "tcp:%i" % port
    else:
        strport = "tcp:%i:interface=%s" % (port, ip)
    listener = tub.listenOn(strport)
    
    return tub, listener

def make_client_service(controller_service, config):
    """
    Create a service that will listen for clients.
    
    This service is simply a `foolscap.Tub` instance that has a set of Referenceables
    registered with it.
    """

    # Now create the foolscap tub
    ip = config['controller']['client_tub']['ip']
    port = config['controller']['client_tub'].as_int('port')
    location = config['controller']['client_tub']['location']
    secure = config['controller']['client_tub']['secure']
    cert_file = config['controller']['client_tub']['cert_file']
    client_tub, client_listener = make_tub(ip, port, secure, cert_file)
    
    # Set the location in the trivial case of localhost
    if ip == 'localhost' or ip == '127.0.0.1':
        location = "127.0.0.1"
    
    if not secure:
        log.msg("WARNING: you are running the controller with no client security")
    
    def set_location_and_register():
        """Set the location for the tub and return a deferred."""

        def register(empty, ref, furl_file):
            # We create and then move to make sure that when the file
            # appears to other processes, the buffer has the flushed
            # and the file has been closed
            temp_furl_file = get_temp_furlfile(furl_file)
            client_tub.registerReference(ref, furlFile=temp_furl_file)
            os.rename(temp_furl_file, furl_file)
        
        if location == '':
            d = client_tub.setLocationAutomatically()
        else:
            d = defer.maybeDeferred(client_tub.setLocation, "%s:%i" % (location, client_listener.getPortnum()))
        
        for ciname, ci in config['controller']['controller_interfaces'].iteritems():
            log.msg("Adapting Controller to interface: %s" % ciname)
            furl_file = ci['furl_file']
            log.msg("Saving furl for interface [%s] to file: %s" % (ciname, furl_file))
            check_furl_file_security(furl_file, secure)
            adapted_controller = import_item(ci['controller_interface'])(controller_service)
            d.addCallback(register, import_item(ci['fc_interface'])(adapted_controller), 
                furl_file=ci['furl_file'])
    
    reactor.callWhenRunning(set_location_and_register)
    return client_tub


def make_engine_service(controller_service, config):
    """
    Create a service that will listen for engines.
    
    This service is simply a `foolscap.Tub` instance that has a set of Referenceables
    registered with it.
    """

    # Now create the foolscap tub
    ip = config['controller']['engine_tub']['ip']
    port = config['controller']['engine_tub'].as_int('port')
    location = config['controller']['engine_tub']['location']
    secure = config['controller']['engine_tub']['secure']
    cert_file = config['controller']['engine_tub']['cert_file']
    engine_tub, engine_listener = make_tub(ip, port, secure, cert_file)
    
    # Set the location in the trivial case of localhost
    if ip == 'localhost' or ip == '127.0.0.1':
        location = "127.0.0.1"
    
    if not secure:
        log.msg("WARNING: you are running the controller with no engine security")
    
    def set_location_and_register():
        """Set the location for the tub and return a deferred."""

        def register(empty, ref, furl_file):
            # We create and then move to make sure that when the file
            # appears to other processes, the buffer has the flushed
            # and the file has been closed
            temp_furl_file = get_temp_furlfile(furl_file)
            engine_tub.registerReference(ref, furlFile=temp_furl_file)
            os.rename(temp_furl_file, furl_file)
        
        if location == '':
            d = engine_tub.setLocationAutomatically()
        else:
            d = defer.maybeDeferred(engine_tub.setLocation, "%s:%i" % (location, engine_listener.getPortnum()))
    
        furl_file = config['controller']['engine_furl_file']
        engine_fc_interface = import_item(config['controller']['engine_fc_interface'])
        log.msg("Saving furl for the engine to file: %s" % furl_file)
        check_furl_file_security(furl_file, secure)
        fc_controller = engine_fc_interface(controller_service)
        d.addCallback(register, fc_controller, furl_file=furl_file)
    
    reactor.callWhenRunning(set_location_and_register)
    return engine_tub
    
def start_controller():
    """
    Start the controller by creating the service hierarchy and starting the reactor.
    
    This method does the following:
    
        * It starts the controller logging
        * In execute an import statement for the controller
        * It creates 2 `foolscap.Tub` instances for the client and the engines
          and registers `foolscap.Referenceables` with the tubs to expose the
          controller to engines and clients.
    """
    config = kernel_config_manager.get_config_obj()
    
    # Start logging
    logfile = config['controller']['logfile']
    if logfile:
        logfile = logfile + str(os.getpid()) + '.log'
        try:
            openLogFile = open(logfile, 'w')
        except:
            openLogFile = sys.stdout
    else:
        openLogFile = sys.stdout
    log.startLogging(openLogFile)
    
    # Execute any user defined import statements
    cis = config['controller']['import_statement']
    if cis:
        try:
            exec cis in globals(), locals()
        except:
            log.msg("Error running import_statement: %s" % cis)
    
    # Delete old furl files unless the reuse_furls is set
    reuse = config['controller']['reuse_furls']
    if not reuse:
        paths = (config['controller']['engine_furl_file'],
            config['controller']['controller_interfaces']['task']['furl_file'],
            config['controller']['controller_interfaces']['multiengine']['furl_file']
        )
        for p in paths:
            if os.path.isfile(p):
                os.remove(p)
    
    # Create the service hierarchy
    main_service = service.MultiService()
    # The controller service
    controller_service = controllerservice.ControllerService()
    controller_service.setServiceParent(main_service)
    # The client tub and all its refereceables
    client_service = make_client_service(controller_service, config)
    client_service.setServiceParent(main_service)
    # The engine tub
    engine_service = make_engine_service(controller_service, config)
    engine_service.setServiceParent(main_service)
    # Start the controller service and set things running
    main_service.startService()
    reactor.run()

def init_config():
    """
    Initialize the configuration using default and command line options.
    """
    
    parser = OptionParser("""ipcontroller [options]

Start an IPython controller.

Use the IPYTHONDIR environment variable to change your IPython directory 
from the default of .ipython or _ipython.  The log and security 
subdirectories of your IPython directory will be used by this script 
for log files and security files.""")
    
    # Client related options
    parser.add_option(
        "--client-ip", 
        type="string",
        dest="client_ip",
        help="the IP address or hostname the controller will listen on for client connections"
    )
    parser.add_option(
        "--client-port", 
        type="int", 
        dest="client_port",
        help="the port the controller will listen on for client connections"
    )    
    parser.add_option(
        '--client-location',
        type="string",
        dest="client_location",
        help="hostname or ip for clients to connect to"
    )
    parser.add_option(
        "-x",
        action="store_false",
        dest="client_secure",
        help="turn off all client security"
    )
    parser.add_option(
        '--client-cert-file',
        type="string",
        dest="client_cert_file",
        help="file to store the client SSL certificate"
    )
    parser.add_option(
        '--task-furl-file',
        type="string",
        dest="task_furl_file",
        help="file to store the FURL for task clients to connect with"
    )
    parser.add_option(
        '--multiengine-furl-file',
        type="string",
        dest="multiengine_furl_file",
        help="file to store the FURL for multiengine clients to connect with"
    )
    # Engine related options
    parser.add_option(
        "--engine-ip", 
        type="string",
        dest="engine_ip",
        help="the IP address or hostname the controller will listen on for engine connections"
    )
    parser.add_option(
        "--engine-port", 
        type="int", 
        dest="engine_port",
        help="the port the controller will listen on for engine connections"
    )    
    parser.add_option(
        '--engine-location',
        type="string",
        dest="engine_location",
        help="hostname or ip for engines to connect to"
    )
    parser.add_option(
        "-y",
        action="store_false",
        dest="engine_secure",
        help="turn off all engine security"
    )
    parser.add_option(
        '--engine-cert-file',
        type="string",
        dest="engine_cert_file",
        help="file to store the engine SSL certificate"
    )
    parser.add_option(
        '--engine-furl-file',
        type="string",
        dest="engine_furl_file",
        help="file to store the FURL for engines to connect with"
    )
    parser.add_option(
        "-l", "--logfile",
        type="string",
        dest="logfile",
        help="log file name (default is stdout)"
    )
    parser.add_option(
        "-r",
        action="store_true",
        dest="reuse_furls",
        help="try to reuse all furl files"
    )
    
    (options, args) = parser.parse_args()
    
    config = kernel_config_manager.get_config_obj()
    
    # Update with command line options
    if options.client_ip is not None:
        config['controller']['client_tub']['ip'] = options.client_ip
    if options.client_port is not None:
        config['controller']['client_tub']['port'] = options.client_port
    if options.client_location is not None:
        config['controller']['client_tub']['location'] = options.client_location
    if options.client_secure is not None:
        config['controller']['client_tub']['secure'] = options.client_secure
    if options.client_cert_file is not None:
        config['controller']['client_tub']['cert_file'] = options.client_cert_file
    if options.task_furl_file is not None:
        config['controller']['controller_interfaces']['task']['furl_file'] = options.task_furl_file
    if options.multiengine_furl_file is not None:
        config['controller']['controller_interfaces']['multiengine']['furl_file'] = options.multiengine_furl_file
    if options.engine_ip is not None:
        config['controller']['engine_tub']['ip'] = options.engine_ip
    if options.engine_port is not None:
        config['controller']['engine_tub']['port'] = options.engine_port
    if options.engine_location is not None:
        config['controller']['engine_tub']['location'] = options.engine_location
    if options.engine_secure is not None:
        config['controller']['engine_tub']['secure'] = options.engine_secure
    if options.engine_cert_file is not None:
        config['controller']['engine_tub']['cert_file'] = options.engine_cert_file
    if options.engine_furl_file is not None:
        config['controller']['engine_furl_file'] = options.engine_furl_file
    if options.reuse_furls is not None:
            config['controller']['reuse_furls'] = options.reuse_furls

    if options.logfile is not None:
        config['controller']['logfile'] = options.logfile
    
    kernel_config_manager.update_config_obj(config)

def main():
    """
    After creating the configuration information, start the controller.
    """
    init_config()
    start_controller()
    
if __name__ == "__main__":
    main()
