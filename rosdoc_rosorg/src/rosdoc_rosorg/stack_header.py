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

    if 0:
        # Try to get VCS repo info
        vcs, repo = roslib.vcs.guess_vcs_uri(roslib.stacks.get_stack_dir(s))
        if repo is not None:
            d['repository'] = repo
            d['vcs'] = vcs
    else:
        #TODO: guess code URI
        d['vcs'] = repo.type
        d['repository'] = repo.name

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

    print "writing stack properties to", filename
    with codecs.open(filename, mode='w', encoding='utf-8') as f:
        f.write(yaml.dump(d))
  

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
