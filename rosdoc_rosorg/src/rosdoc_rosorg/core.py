import yaml

def load_repos(filename):
    with open(filename) as f:
        data = yaml.load(f.read())
    # rosinstall file is a list of dictionaries
    repos = []
    for d in data:
        type_ = d.keys()[0]
        config = d[type_]
        
        name = config['local-name']
        uri  = config['uri']

        r = Repo(name, type_, uri)
        repos.append(r)
    
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

