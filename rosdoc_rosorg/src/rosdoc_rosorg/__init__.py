#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2008, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Revision $Id: __init__.py 10740 2010-08-18 00:52:44Z tfoote $

import sys
import os
import time
import traceback
from subprocess import Popen, PIPE

NAME='rosdoc'

from rdcore import *
import rosdoc.upload

def main():
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog [options] [packages...]", prog=NAME)
    parser.add_option("-n", "--name",metavar="NAME",
                      dest="name", default="ROS Package", 
                      help="Name for documentation set")
    parser.add_option("-q", "--quiet",action="store_true", default=False,
                      dest="quiet",
                      help="Suppress doxygen errors")
    parser.add_option("--paths",metavar="PATHS",
                      dest="paths", default=None, 
                      help="package paths to document")
    parser.add_option("-o",metavar="OUTPUT_DIRECTORY",
                      dest="docdir", default='doc', 
                      help="directory to write documentation to")
    parser.add_option("--repos", default=None,
                      dest="repos", metavar="ROSBROWSE_REPOS_FILE",
                      help="repos list from rosbrowse for determining repository names/roots")
    parser.add_option("--upload",action="store", default=None,
                      dest="upload", metavar="RSYNC_TARGET",
                      help="rsync target argument")

    options, package_filters = parser.parse_args()

    # Load the ROS environment - repos is for the rosdoc build on
    # Hudson. It generates the correct repository roots for generating
    # package_headers
    repos = None
    if options.repos:
        with open(options.repos, 'r') as f:
            # load file
            repos = [l.split() for l in f if not l.startswith('#')]
            # convert to dictionary
            repos = dict([(key, (type, uri)) for key, type, uri in repos])

    ctx = RosdocContext(options.name, options.docdir,
                        package_filters=package_filters, path_filters=options.paths,
                        repos=repos)

    try:
        ctx.init()

        rosdoc.generate_docs(ctx)
        
        stack_dirs = []

        import package_header
        package_header.generate_package_headers(ctx)
        stack_files = package_header.generate_stack_headers(ctx)
        stack_dirs = [os.path.dirname(f) for f in stack_files]
        if options.upload:
            print success, stack_dirs
            rosdoc.upload.upload(success + stack_dirs + ['index.html', 'licenses.html', 'styles.css'], options.upload)

    except:
        traceback.print_exc()
        sys.exit(1)
