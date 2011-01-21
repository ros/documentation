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
from . import repo_header
from . import megamanifest
from . import megastack

def generate_docs(ctx, repos, checkout_dir, test=False):
    if not test:
        # when we are testing just rosdoc_rosorg, we don't want to do
        # the more expensive rosdoc build
        artifacts = rosdoc.generate_docs(ctx)
    else:
        artifacts = []

    stack_dirs = []
    
    timings = ctx.timings
    timings['package-header'] = 0.
    timings['stack-header'] = 0.
    timings['repo-header'] = 0.

    # first package/stack to be documented wins
    completed_packages = set()
    completed_stacks = set()
    
    for repo_name, repo in repos:
        if test:
            continue
        print "repo", repo_name
        # workaround for ros aliasing
        if repo_name == 'ros':
            repo_dir = os.path.join(checkout_dir, 'ros-repo')
        else:
            repo_dir = os.path.join(checkout_dir, repo_name)
            
        if not os.path.exists(repo_dir):
            print >> sys.stderr, "checkout [%s] doesn't exist"%(repo_dir)
            continue

        # Packages
        start = time.time()
        packages = roslib.packages.list_pkgs_by_path(repo_dir)
        # ros-repo doesn't include the ros stack, so we have to add it back in
        if repo_name == 'ros':
            packages = packages + roslib.stacks.packages_of('ros')
        # only document requested packages, and don't document anything already documented (name collisions)
        packages = list(set(packages) & set(ctx.packages) - completed_packages)

        print "[%s] Generating manifest.yaml files for [%s]"%(repo_name, ','.join(packages))
        package_files = package_header.generate_package_headers(ctx, repo, packages)
        timings['package-header'] += time.time() - start
        
        # Stacks
        start = time.time()
        stacks = roslib.stacks.list_stacks_by_path(repo_dir)
        if repo_name == 'ros':
            stacks.append('ros')
        # only document requested stacks, and don't document anything
        # already documented (name collisions)
        stacks = list((set(stacks) & set(ctx.stacks)) - completed_stacks)
        timings['stack-header'] += time.time() - start
        
        # - generate
        print "[%s] Generating stack.yaml files for [%s]"%(repo_name, ','.join(stacks))
        stack_files = stack_header.generate_stack_headers(ctx, repo, stacks)
        # - simplify artifacts to the directory name
        stack_dirs.extend([os.path.dirname(f) for f in stack_files])

        start = time.time()
        artifacts.extend(repo_header.generate_repo_header(ctx, repo, stack_files, package_files))
        timings['repo-header'] += time.time() - start

        completed_packages.update(packages)
        completed_stacks.update(stacks)        
    
    # we don't include package artifacts because they are already covered elsewhere
    return artifacts + stack_dirs

def generate_rosbrowse(ctx, repos, checkout_dir, test=False):
    timings = ctx.timings
    timings['megamanifest'] = 0.
    timings['megastack'] = 0.

    artifacts = []
    try:
        start = time.time()
        artifacts.extend(megamanifest.generate_megamanifest(ctx, repos, checkout_dir))
        timings['megamanifest'] += time.time() - start
        
        start = time.time()
        artifacts.extend(megastack.generate_megastack(ctx, repos, checkout_dir))
        timings['megastack'] += time.time() - start        
    except:
        print >> sys.stderr, "megamanifest generation failed"
        traceback.print_exc()
        
    return artifacts
    
def rosorg_main():
    parser = rosdoc.get_optparse('rosdoc_rosorg')
    parser.add_option("--repos", default=None,
                      dest="repos", metavar="ROSBROWSE_REPOS_FILE",
                      help="repos list from rosbrowse for determining repository names/roots")
    parser.add_option("--checkout", default='checkouts',
                      dest="checkout_dir", metavar="CHECKOUT_DIR",
                      help="path to checkout directory for repos file")
    parser.add_option("--test", default=False,
                      dest="test", action="store_true",
                      help="run in test mode")
    parser.add_option("--rosbrowse", default=False,
                      dest="rosbrowse", action="store_true",
                      help="run rosbrowse indexer instead")

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
        ctx.quiet = options.quiet        
        ctx.init()

        if not options.rosbrowse:
            artifacts = generate_docs(ctx, repos, options.checkout_dir, options.test)
        else:
            artifacts = generate_rosbrowse(ctx, repos, options.checkout_dir)
            
        if options.upload:
            rosdoc.upload.upload(ctx, artifacts, options.upload)

        print "Timings"
        for k, v in ctx.timings.iteritems():
            print " * %.2f %s"%(v, k)
            
    except KeyboardInterrupt:
        pass
    except:
        traceback.print_exc()
        sys.exit(1)
