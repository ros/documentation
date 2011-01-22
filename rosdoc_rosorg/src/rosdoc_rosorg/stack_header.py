# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Willow Garage, Inc.
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
# $Author$

"""
The stack header is a YAML file that is used by the ROS.org wiki as
well as rosinstall.  It is similar in concept to the stack manifest
(stack.xml), but it contains additional data and is in YAML format for
easier processing in python scripts.

The data in the stack header is not formally specified, but includes:

 * manifest data (description, license, author, depends, review status, url)
 * rosinstall configuration information (VCS URI, branches, etc...)
 * packages in stack
 * depends-on information
"""

import os
import sys
import codecs
import traceback

import yaml

import vcstools
import roslib.rospack
import roslib.stacks
import vcstools

from .core import Repo

def _generate_stack_headers(ctx, filename, s, repo):
    m = ctx.stack_manifests[s]
    d = {
      'brief': m.brief,
      'description': m.description.strip() or '',
      'license': m.license or '',
      'authors': m.author or '',
      'depends': [d.stack for d in m.depends],
      'review_status': m.status or '',
      'review_notes': m.notes or '',
      'url': m.url,
      'packages': roslib.stacks.packages_of(s),
      'depends_on': roslib.rospack.rosstack_depends_on_1(s),
      }

    d['vcs'] = repo.type
    d['repository'] = repo.name
    d['rosinstall'] = repo.rosinstall.copy()
    if repo.type == 'svn':
        # svn allows partial checkouts, DVCSs generally don't
        d['vcs_uri'] = vcstools.get_svn_url(roslib.stacks.get_stack_dir(s))
        # update svn rules
        d['rosinstall']['svn']['uri'] = d['vcs_uri']
    elif repo.type == 'git':
        repo_type, repo_uri = vcstools.guess_vcs_uri(roslib.stacks.get_stack_dir(s))
        d['vcs_uri'] = repo_uri
        # update git rules
        d['rosinstall']['git']['uri'] = repo_uri
    else:
        d['vcs_uri'] = repo.uri

    # encode unicode entries
    d_copy = d.copy()
    for k, v in d_copy.iteritems():
        if isinstance(v, basestring):
            try:
                d[k] = v.encode("utf-8")
            except UnicodeDecodeError, e:
                print >> sys.stderr, "error: cannot encode value for key", k
                d[k] = ''
        elif type(v) == list:
            try:
                d[k] = [x.encode("utf-8") for x in v]
            except UnicodeDecodeError, e:
                print >> sys.stderr, "error: cannot encode value for key", k
                d[k] = []

    if not ctx.quiet:
        print "writing stack properties to", filename
    with codecs.open(filename, mode='w', encoding='utf-8') as f:
        f.write(yaml.safe_dump(d))
  

def generate_stack_headers(ctx, repo, stacks):
    """
    Generate stack.yaml files for MoinMoin PackageHeader macro

    @return: list of stack.yaml files
    @rtype: [str]
    """
    artifacts = []
    for s in stacks:
        
        filename = os.path.join(ctx.docdir, s, 'stack.yaml')
        filename_dir = os.path.dirname(filename)
        if not os.path.isdir(filename_dir):
            os.makedirs(filename_dir)
        artifacts.append(filename)
        
        try:
            #print "generating stack wiki files for", s
            _generate_stack_headers(ctx, filename, s, repo)
        except Exception, e:
            traceback.print_exc()
            print >> sys.stderr, "Unable to generate stack.yaml for %s: %s"%(s, e)

    return artifacts
