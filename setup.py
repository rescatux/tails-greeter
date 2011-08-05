#!/usr/bin/env python
#
# Copyright 2011 Max <govnototalitarizm@gmail.com>
# Copyright (C) 2009 Martin Owens
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

from distutils.core import setup
from DistUtilsExtra.command import *
from fnmatch import fnmatch

__appname__ = 'tails-greeter'
__version__ = '0.0.6'
import os, platform

# remove MANIFEST. distutils doesn't properly update it
# when the contents of directories change.
if os.path.exists('MANIFEST'): os.remove('MANIFEST')

if platform.system() == 'FreeBSD':
        man_dir = 'man'
else:
        man_dir = 'share/man'

def listfiles(*dirs):
        dir, pattern = os.path.split(os.path.join(*dirs))
        return [os.path.join(dir, filename)
                for filename in os.listdir(os.path.abspath(dir))
                        if filename[0] != '.' and fnmatch(filename, pattern)]

# Generate a standard share dir
SDIR = 'share/%s/' % __appname__

setup(
        name             = __appname__,
        version          = __version__,
        description      = 'Shows a community lab loging screen',
        long_description = "Replaces the traditional gdm with a new community cener specialised version.",
        author           = 'Max S',
        author_email     = 'govnototalitarizm@gmail.com',
        url              = 'https://tails.boum.org/todo/TailsGreeter/',
        platforms        = 'linux',
        license          = 'GPLv3',
        packages         = [ 'GdmGreeter', 'gtkme', 'xsdvalidate', 'xsdvalidate.parse' ],
        scripts          = [ 'tails-greeter' ],
        data_files       = [
            ( SDIR, listfiles( '', '*.py' ) ),
            ( SDIR + 'glade', listfiles( 'glade', '*.glade' ) ),
            ( SDIR + 'pixmaps', listfiles( 'pixmaps', '*.svg' ) ),
            ( SDIR + 'pixmaps/lang', listfiles( 'pixmaps/lang', '*.*' ) ),
            ( SDIR + 'pixmaps/theme', listfiles( 'pixmaps/theme', '*.*' ) ),
            ( SDIR + 'pixmaps/auto', listfiles( 'pixmaps/auto', '*.*' ) ),
            ( 'share/gdm/autostart/LoginWindow/', [ 'tails-greeter.desktop' ] ),
            ( 'bin/', [ 'tails-lang-helper' ] ),
            ( SDIR, [ 'tails-logging.conf' ] ),
        ],
        cmdclass={
                   'build'       : build_extra.build_extra,
                   'build_i18n'  : build_i18n.build_i18n,
                 },
    )

