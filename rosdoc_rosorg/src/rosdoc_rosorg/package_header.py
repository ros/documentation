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
from __future__ import with_statement

import codecs
import os
import sys
import traceback
import yaml

import roslib.msgs
import roslib.rospack
import roslib.srvs
import roslib.stacks
import roslib.packages
import roslib.vcs

from .core import package_link

def _generate_package_headers(ctx, repo, p, filename):
    m = ctx.manifests[p]
    m.description = m.description or ''
    d = {
        'brief': m.brief,
        'description': m.description.strip() or '',
        'license': m.license or '',
        'authors': m.author or '',
        'depends': [d.package for d in m.depends],
        'review_status': m.status or '',
        'review_notes': m.notes or '',
        'url': m.url,
        }
  
    if m.versioncontrol:
        d['version_control'] = m.versioncontrol.url
          
    siblings = []
    stack = roslib.stacks.stack_of(p) or ''
    if stack:
        d['stack'] = stack
        d['siblings'] = roslib.stacks.packages_of(stack)
  
    d['depends_on'] = roslib.rospack.rospack_depends_on_1(p)
      
    d['api_documentation'] = package_link(p)
  
    if p in ctx.external_docs:
        d['external_documentation'] = ctx.external_docs[p]
  
    d['msgs'] = roslib.msgs.list_msg_types(p, False)
    d['srvs'] = roslib.srvs.list_srv_types(p, False)        
  
    d['dependency_tree'] = package_link(p) + '%s_deps.pdf'%p
  
    # encode unicode entries. This is probably overkill, but it was hard
    # hunting the unicode encoding issues down
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
                
    # Try to get VCS repo info
    if repo is not None:
        d['repository'] = repo.name
        d['vcs'] = repo.type
  
    with codecs.open(filename, mode='w', encoding='utf-8') as f:
        f.write(yaml.dump(d))
    
def generate_package_headers(ctx, repo, packages):
    """
    Generate manifest.yaml files for MoinMoin PackageHeader macro
    """
    try:
        import yaml
    except ImportError:
        print >> sys.stderr, "Cannot import yaml, will not generate MoinMoin PackageHeader files"
        return

    artifacts = []
    for p in packages:
        if not ctx.should_document(p):
            continue

        filename = os.path.join(ctx.docdir, p, 'manifest.yaml')
        filename_dir = os.path.dirname(filename)
        if not os.path.isdir(filename_dir):
            os.makedirs(filename_dir)

        try:
            if not ctx.quiet:
                print "writing package properties to", filename
            _generate_package_headers(ctx, repo, p, filename)
            artifacts.append(filename)
        except Exception, e:
          traceback.print_exc()
          print >> sys.stderr, "Unable to generate manifest.yaml for "+p+str(e)

    # TODO: generate repo-specific artifact list
    return artifacts
