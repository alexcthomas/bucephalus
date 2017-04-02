import os, pdb, copy
import ujson, yaml

class JSONViewBuilder(object):
    """
    class for building and providing view definitions
    can do things like auto-rebuild when files change
    """

    def __init__(self, loc):
        self.location = loc
        self.views_cache = {}
        self.allowed_types = ['json','yaml']

        self.read_views()
        self.build_views()

    def read_views(self):
        for r, dirs, files in os.walk(self.location):
            for file_name in files:

                view_name,_,typ = file_name.rpartition('.')
                file_path = os.path.join(r, file_name)

                # check we accept views in that language
                if typ not in self.allowed_types:
                    continue

                # check if we have a cached version
                if view_name in self.views_cache:
                    cached = self.views_cache[view_name]

                    # check this isn't a duplicate
                    if r != cached['path']:
                        msg = 'View {}, in {} is duplicated in {}'
                        raise RuntimeError(msg.format(view_name, cached['path'], r))

                    # check this is newer than the cached copy
                    mtime = os.stat(file_path).mtime
                    if mtime <= cached.get('mtime', 1e12):
                        continue

                # read the view
                mtime = os.stat(file_path).st_mtime
                v = self.read_view(typ, file_path)
                obj = {'view': v, 'mtime': mtime, 'path': file_path}
                self.views_cache[view_name] = obj


    def read_view(self, typ, pth):
        with open(pth, 'r') as fh:
            if typ == 'json':
                return ujson.load(fh)
            if typ == 'yaml':
                return yaml.load(fh)


    def build_views(self):
        """
        function for building view definitions
        recursive templating not yet implemented
        """
        pass


    def get_view(self, viewname):
        return copy.deepcopy(self.views_cache[viewname]['view'])
