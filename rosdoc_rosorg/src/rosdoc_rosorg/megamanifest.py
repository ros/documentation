# Software License Agreement (BSD License)
#
# Copyright (c) 2010, Willow Garage, Inc.
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
# Revision $Id: generate_megamanifest.py 12303 2010-11-23 16:43:34Z kwc $

import os
import sys
import traceback
from subprocess import call, check_call, Popen

from xml.dom.minidom import getDOMImplementation, parse
import roslib.packages
import vcstools
from roslib.manifest import MANIFEST_FILE

def generate_megamanifest(ctx, repos, checkouts_dir):
    all_pkgs = { }
    for repo_name, repo in repos:
        name = repo_name
        vcs = repo.type
        uri = repo.uri

        print "snarfing manifests in local copy of %s"%name
        rel_path = os.path.join(checkouts_dir, name)
        abs_co_path = os.path.abspath(rel_path)
        # cache paths into repo_pkgs
        repos_pkgs = {}
        for pkg in roslib.packages.list_pkgs_by_path(rel_path, cache=repos_pkgs):
            if pkg not in all_pkgs:
                # de-resolve externals #2456. This logic assumes that the
                # vcs is SVN and that they URLs are consistently
                # specified. It will probably take a lot more logic to get
                # this perfectly right
                override_path = None
                true_uri = uri
                try:
                    pkg_path = repos_pkgs[pkg][0]
                    if vcs == 'svn':
                        vcs0, true_uri = vcstools.guess_vcs_uri(pkg_path)
                        # rel_path is incorrect if true_uri doesn't
                        # match. recompute rel_path by getting URL of package
                        # and slicing.

                        if true_uri != uri:
                            url_path = vcstools.get_svn_url(pkg_path)
                            override_path = url_path[len(true_uri):]
                        else:
                            # list_pkgs_by_path converts paths to abspath to avoid some path bugs.
                            # this requires us to always override. 
                            # In the future, the format should just assume absolute URLs instead of composing URLs
                            pkg_path = os.path.abspath(pkg_path)
                            override_path = pkg_path[len(abs_co_path):]
                    else:
                        #DVCS systems don't allow URL sub-indexing
                        override_path = ''
                        if vcs == 'git': 
                            # give the package the uri of its submodule, if appropriate 
                            vcs1, true_uri = vcstools.guess_vcs_uri(stack_path) 
                            if 'github.com/' in uri and uri.endswith('.git'):
                                true_uri = uri[:-4]
                except:
                    traceback.print_exc()
                    pass
                all_pkgs[pkg] = [pkg, name, true_uri, pkg_path, override_path]

    pkgs_dom = getDOMImplementation().createDocument(None, 'pkgs', None)
    pkgs_node = pkgs_dom.documentElement

    for k, v in all_pkgs.iteritems():
        pkg, repo, uri, rel_path, override_path = v
        manifest_p = rel_path+os.sep+MANIFEST_FILE
        try:
            manifest = parse(manifest_p)
            manifest_node = manifest.documentElement
            manifest_node.setAttribute("name", k)
            manifest_node.setAttribute("repo", repo)
            manifest_node.setAttribute("repo_host", uri)
            #TODO: change all this just to use absolute URLs. rel-path generation is too unstable
            base_rel_path = os.path.join(checkouts_dir, name)            
            rel_path = rel_path[len(base_rel_path):]
            if override_path is not None:
                manifest_node.setAttribute("path", override_path)
            else:
                manifest_node.setAttribute("path", rel_path)
                
            pkgs_node.appendChild(manifest_node)
        except:
            traceback.print_exc()
            print "error parsing %s"%manifest_p

    print "writing megamanifest..."
    fname = os.path.join(ctx.docdir, 'megamanifest.xml')
    with open(fname, 'w') as f:
        f.write(pkgs_node.toxml(encoding='utf-8'))
    return [fname]
