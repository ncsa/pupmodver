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
        print( "...self.has_update()")
        pprint.pprint( self )
        rv = False
        if self.installed_version and self.latest_version():
            pprint.pprint( self.installed_version )
            pprint.pprint( self._latest_version )
            cur = distutils.version.LooseVersion( self.installed_version )
            new = distutils.version.LooseVersion( self._latest_version )
            rv = cur < new
        return rv


    def __str__( self ):
        return '<{c} {n} ({i}) [{l}]>'.format( 
            c=self.__class__.__name__,
            n=self.name,
            i=self.installed_version,
            l=self._latest_version
            )

    __repr__ = __str__


def construct_ruby_object(loader, suffix, node):
    return loader.construct_yaml_map(node)

def construct_ruby_sym(loader, node):
    return loader.construct_yaml_str(node)


#def get_current_version( forgename ):
#    # forgename has a fwd slash, replace with a dash for API URL
#    apiname = forgename.replace( '/', '-' )
#    url = 'https://forge.puppetlabs.com:443/v3/modules/{}'.format( apiname )
#    response = requests.get(url)
#    if response.status_code != 200:
#        response.raise_for_status()
#        #raise ApiError('GET ' + moduleURL + '{}'.format(response.status_code))    
#    version = response.json()['current_release']['version']
#    return version
    

def get_local_puppet_modules( env ):
    # get yaml data from local puppet instance
    puppetPath = "/opt/puppetlabs/bin/puppet"
    cmd = [ puppetPath ]
    args = [ "module", "list", "--render-as", "yaml" ]
    myPuppet = subprocess.check_output( cmd + args )
    data = list( yaml.load_all(myPuppet) )[0]
    # first path is the environment specific path
    path = data[ ':environment' ][ 'modulepath' ][0]
    mod_data_list = data[ ':modules_by_path' ][ path ]
    # parse yaml data into a list of PuppetModule objects
    local_modules = []
    for modhash in mod_data_list:
#        pprint.pprint( modhash )
        m = PuppetModule()
        m.name = modhash[ 'name' ]
        try:
            m.forgename = modhash[ 'forge_name' ]
            m.installed_version = modhash[ 'version' ]
        except ( KeyError ) as e:
            pass
#        pprint.pprint( m )
        local_modules.append( m )
    return local_modules


def process_cmdline():
    parser = argparse.ArgumentParser( description='Get puppet module versions' )
    parser.add_argument( '-e', '--environment' )
    parser.add_argument( '-u', '--updates-only', action='store_true',
        help='Show only modules with available updates' )
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
                print( m )
        else:
            print( m )
#    #local_data = list( get_local_puppet_modules() )[0]
#    #pprint.pprint( local_data, depth=4 )
#    modules_by_path = local_data[ ':modules_by_path' ]
#    for module_list in modules_by_path.values():
#        for m in module_list:
#            if 'forge_name' in m and 'version' in m:
#                fname = m['forge_name']
#                installed_version = distutils.version.LooseVersion( m['version'] )
#                #installed_version = m['version']
#                try:
#                    latest_version = distutils.version.LooseVersion( get_current_version( fname ) )
#                except ( requests.exceptions.HTTPError ) as e:
#                    continue
#                status = 'OK'
#                if installed_version < latest_version:
#                    status = 'UPGRADE'
#                print( '{:7s} {:33s} [{:8s}] ({:8s})'.format( status, fname, installed_version, latest_version ) )


if __name__ == "__main__":
    run()
