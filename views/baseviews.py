
class BaseViewBuilder(object):
    """
    Base view class, providing a common interface
    """

    def list_views(self):
        return sorted(self.views_cache.keys())

    def has_view(self, typ):
        return typ in self.views_cache
