#!venv/bin/python

from __future__ import print_function

import yaml
import re
import requests
import subprocess
import sys
import distutils.version
import argparse

import pprint

class PuppetModule( object ):
    keys = [ 'name', 'forgename', 'installed_version', '_latest_version' ]
    def __init__( self, *a, **k ):
        for key in self.keys:
            setattr( self, key, None )
        for key in k:
            if key in self.keys:
                setattr( self, key, k[key] )
        self.apiname = None
        self.is_from_forge = None

    def latest_version( self ):
        if not self.forgename:
            return None
        if not self._latest_version:
            if not self.apiname:
                self.apiname = self.forgename.replace( '/', '-' )
            url = 'https://forge.puppetlabs.com:443/v3/modules/{}'.format( self.apiname )
            response = requests.get(url)
            if response.status_code != 200:
                self.is_from_forge = False
                self._latest_version = None
            else:
                self.is_from_forge = True
                self._latest_version = response.json()['current_release']['version']
            #self._latest_version = distutils.version.LooseVersion( l_ver )
        return self._latest_version


    def has_update( self ):
        rv = False
        if self.installed_version and self.latest_version():
            cur = distutils.version.LooseVersion( self.installed_version )
            new = distutils.version.LooseVersion( self._latest_version )
            rv = cur < new
        return rv


    def __str__( self ):
        return '<{c} {n} ({i}) [{l}]>'.format( 
            c=self.__class__.__name__,
            n=self.name,
            i=self.installed_version,
            l=self.latest_version()
            )

    __repr__ = __str__


def construct_ruby_object(loader, suffix, node):
    return loader.construct_yaml_map(node)

def construct_ruby_sym(loader, node):
    return loader.construct_yaml_str(node)
    

def get_local_puppet_modules( env ):
    # get yaml data from local puppet instance
    puppetPath = "/opt/puppetlabs/bin/puppet"
    cmd = [ puppetPath ]
    args = [ "module", "list", "--environment", str( env ), "--render-as", "yaml" ]
    myPuppet = subprocess.check_output( cmd + args )
    data = list( yaml.load_all(myPuppet) )[0]
    # first path is the environment specific path
    path = data[ ':environment' ][ 'modulepath' ][0]
    mod_data_list = data[ ':modules_by_path' ][ path ]
    # parse yaml data into a list of PuppetModule objects
    local_modules = []
    for modhash in mod_data_list:
        m = PuppetModule()
        m.name = modhash[ 'name' ]
        try:
            m.name = modhash[ 'metadata' ][ 'name' ]
        except ( KeyError ) as e:
            pass
        try:
            m.forgename = modhash[ 'forge_name' ]
            m.installed_version = modhash[ 'version' ]
        except ( KeyError ) as e:
            pass
        local_modules.append( m )
    return local_modules


def print_module( args, m ):
    if args.terse:
        print( m.name )
    else:
        print( m )


def process_cmdline():
    parser = argparse.ArgumentParser( description='Get puppet module versions' )
    parser.add_argument( '-e', '--environment' )
    parser.add_argument( '-u', '--updates-only', action='store_true',
        help='Show only modules with available updates' )
    parser.add_argument( '-t', '--terse', action='store_true',
        help='Terse output (list module names only)' )
    args = parser.parse_args()
    return args

    
def run():
    # Add constructors for ruby objects (embedded in yaml output from puppet)
    yaml.add_multi_constructor(u"!ruby/object:", construct_ruby_object)
    yaml.add_constructor(u"!ruby/sym", construct_ruby_sym)

    args = process_cmdline()

    local_modules = get_local_puppet_modules( args.environment )
    for m in local_modules:
        if args.updates_only:
            if m.has_update():
                print_module( args, m )
        else:
            print_module( args, m )


if __name__ == "__main__":
    run()
