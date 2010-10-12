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
# Revision $Id$

import yaml

def load_repos(filename):
    """
    Load repository file, which is a rosinstall file with particular semantics
    
    @return: map of repositories
    @rtype: {str: Repo}
    """
    with open(filename) as f:
        data = yaml.load(f.read())
    # rosinstall file is a list of dictionaries
    repos = {}
    for d in data:
        type_ = d.keys()[0]
        config = d[type_]
        
        name = config['local-name']
        if name == 'ros-repo':
            # due to the way rosinstall works, ros-repo can't be
            # called ros
            name = 'ros'
        uri  = config['uri']

        r = Repo(name, type_, uri)
        repos[name] = r
    return repos
    
class Repo(object):
    
    def __init__(self, name, type_, uri):
        self.name = name
        self.type = type_
        self.uri = uri

_api_url = "http://ros.org/doc/api/"
def package_link(package):
    return _api_url + package + "/html/"
def stack_link(stack):
    return _api_url + stack + "/html/"

