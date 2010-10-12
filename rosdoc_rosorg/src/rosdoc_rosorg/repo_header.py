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
# Revision $Id: package_header.py 11472 2010-10-12 02:08:53Z kwc $
# $Author: kwc $

import os
import sys
import codecs
import traceback

import yaml

import roslib.vcs
import roslib.rospack
import roslib.stacks
import roslib.vcs

from .core import Repo

def generate_repo_header(ctx, repo, stack_files):
    """
    Generate repo.yaml files for MoinMoin Repo macros

    @param stack_files: list of stack.yaml files related to this repo
    @return: list of generate files (a single repo.yaml file)
    @rtype: [str]
    """
    repo_data = {
        'name': repo.name,
        'vcs': {
            'type': repo.type,
            'uri': repo.uri,
            },
        'stacks': {}
        }
    for f in stack_files:
        stack_name = os.path.basename(os.path.dirname(f))
        with open(f) as stack_f:
            d = yaml.load(stack_f)
        repo_data['stacks'][stack_name] = d
        
    filename = os.path.join(ctx.docdir, repo.name, 'repo.yaml')
    filename_dir = os.path.dirname(filename)
    if not os.path.isdir(filename_dir):
        os.makedirs(filename_dir)

    with open(filename, 'w') as f:
        print "generating repo header %s"%(filename)
        f.write(yaml.dump(repo_data))

    return [filename]
