
class BaseViewBuilder(object):
    """
    Base view class, providing a common interface
    """

    def list_views(self):
        return sorted(self.views_cache.keys())

    def has_view(self, typ):
        return typ in self.views_cache

    def requires_client_data(self):
        """
        Returns True if this view requires data on the client (for client-side graphing).  Graphs that
        are generated on the server (e.g. Matplotlib) should return False here.
        :return: 
        """
        return True

