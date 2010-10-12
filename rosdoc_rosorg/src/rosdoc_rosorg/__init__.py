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
# Revision $Id$

import sys
import os
import time
import traceback

import roslib.packages
import roslib.stacks

import rosdoc
import rosdoc.upload

from .core import load_repos
from . import package_header
from . import stack_header


def generate_docs(ctx, repos, checkout_dir):
    if 0:
        artifacts = rosdoc.generate_docs(ctx)
    else:
        artifacts = []

    stack_dirs = []
    
    for repo_name, repo in repos.iteritems():
        repo_dir = os.path.join(checkout_dir, repo_name)

        if 0:
            # Packages
            packages = roslib.packages.list_pkgs_by_path(repo_dir)
            packages = list(set(packages) ^ set(ctx.packages))
            # - ignore package artifacts, they are embedded in normal hiearchy
            _ = package_header.generate_package_headers(ctx, repo, packages)

        # Stacks
        stacks = roslib.stacks.list_stacks_by_path(repo_dir)
        stacks = list(set(stacks) ^ set(ctx.stacks))
        # - generate
        stack_files = stack_header.generate_stack_headers(ctx, repo, stacks)
        # - simplify artifacts to the directory name
        stack_dirs.extend([os.path.dirname(f) for f in stack_files])
    
    return artifacts + stack_dirs

def rosorg_main():
    parser = rosdoc.get_optparse('rosdoc_rosorg')
    parser.add_option("--repos", default=None,
                      dest="repos", metavar="ROSBROWSE_REPOS_FILE",
                      help="repos list from rosbrowse for determining repository names/roots")
    parser.add_option("--checkout", default='checkouts',
                      dest="checkout_dir", metavar="CHECKOUT_DIR",
                      help="path to checkout directory for repos file")

    options, package_filters = parser.parse_args()

    # Load the repository file
    if options.repos:
        repos_file = options.repos
    else:
        repos_file = os.path.join(roslib.packages.get_pkg_dir('rosdoc_rosorg'), 'repos.rosinstall')
    repos = load_repos(repos_file)

    # Load the rosdoc environment
    ctx = rosdoc.RosdocContext(options.name, options.docdir,
                               package_filters=package_filters, path_filters=options.paths)

    try:
        ctx.init()

        artifacts = generate_docs(ctx, repos, options.checkout_dir)
        if options.upload:
            print artifacts
            rosdoc.upload.upload(artifacts, target=options.upload)

        print "Timings"
        for k, v in ctx.timings.iteritems():
            print " * %.2f %s"%(v, k)
            
    except:
        traceback.print_exc()
        sys.exit(1)
