#!/usr/bin/env python
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
# Author: Steven Bellens, Morgan Quigley (adapted from generate_megamanifest.py), kwc
# Revision $Id: generate_megastack.py 12920 2011-01-21 03:15:30Z kwc $

import os
import sys
from subprocess import call, check_call, Popen
import traceback
            
from xml.dom.minidom import getDOMImplementation, parse
import roslib.stacks
import vcstools
from roslib.stacks import STACK_FILE


def generate_megastack(ctx, repos, checkouts_dir):
    all_stacks = { }
    for repo_name, repo in repos:
        name = repo_name
        vcs = repo.type
        uri = repo.uri

        print "snarfing stacks in local copy of %s"%name
        rel_path = os.path.join(checkouts_dir, name)
        abs_co_path = os.path.abspath(rel_path)
        # cache paths into repo_pkgs
        repos_stacks = {}
        for stack in roslib.stacks.list_stacks_by_path(rel_path, cache=repos_stacks):
            if len(stack) == 0:
                print "empty stack name. i assume the uri was a direct stack checkout. using repo name as stack name: [%s]"%name
                stack = name
            if stack not in all_stacks:
                # de-resolve externals #2456. This logic assumes that the
                # vcs is SVN and that they URLs are consistently
                # specified. It will probably take a lot more logic to get
                # this perfectly right
                override_path = None
                true_uri = uri
                stack_path = rel_path
                try:
                    stack_path = repos_stacks[stack]
                    if vcs == 'svn':
                        vcs0, true_uri = vcstools.guess_vcs_uri(stack_path)
                        # rel_path is incorrect if true_uri doesn't
                        # match. recompute rel_path by getting URL of package
                        # and slicing.
                        if true_uri != uri:
                            url_path = vcstools.get_svn_url(stack_path)
                            override_path = url_path[len(true_uri):]
                        else:
                            # list_pkgs_by_path converts paths to abspath to avoid some path bugs.
                            # this requires us to always override. 
                            # In the future, the format should just assume absolute URLs instead of composing URLs
                            stack_path = os.path.abspath(stack_path)
                            override_path = stack_path[len(abs_co_path):]

                    else:
                        #DVCS systems don't allow URL sub-indexing
                        override_path = ''
                        if vcs == 'git': 
                            # give the package the uri of its submodule, if appropriate 
                            vcs1, true_uri = vcstools.guess_vcs_uri(stack_path) 
                            if 'github.com/' in uri and uri.endswith('.git'):
                                true_uri = uri[:-4]
                except:
                    pass
                #print "stack name: %s" % stack
                #print name + " stacks: " + str(roslib.stacks.packages_of(stack))
                try:
                    stack_packages = roslib.stacks.packages_of(stack)
                    all_stacks[stack] = [stack, name, true_uri, stack_path, override_path, stack_packages]
                except roslib.stacks.InvalidROSStackException:
                    print >> sys.stderr, "ignoring stack [%s], environment improperly configured"%(stack)


    stacks_dom = getDOMImplementation().createDocument(None, 'stacks', None)
    stacks_node = stacks_dom.documentElement

    for k, v in all_stacks.iteritems():
        stack, repo, uri, rel_path, override_path, packages = v
        stack_p = rel_path+os.sep+STACK_FILE
        try:
            stack = parse(stack_p)
            stack_node = stack.documentElement
            stack_node.setAttribute("name", k)
            stack_node.setAttribute("repo", repo)
            stack_node.setAttribute("repo_host", uri)
            rel_path = rel_path[len('checkouts/'+repo):]
            if override_path is not None:
                stack_node.setAttribute("path", override_path)
            else:
                stack_node.setAttribute("path", rel_path)            
            for package in packages:
              package_node = stack.createElement("package")
              package_node.setAttribute("name", package)
              stack_node.appendChild(package_node)
            stacks_node.appendChild(stack_node)
        except:
            traceback.print_exc()
            print "error parsing %s"%stack_p

    print "writing megastack ..."
    fname = os.path.join(ctx.docdir, 'megastack2.xml')
    with open(fname, 'w') as f:
        f.write(stacks_node.toxml(encoding='utf-8'))
    return [fname]
