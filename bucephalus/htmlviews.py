from views.baseviews import BaseViewBuilder

class HTMLViewBuilder(BaseViewBuilder):
    """
    HTML views
    """
    def __init__(self):
        self.views_cache = {'explanation': self.explanation}

    def list_views(self):
        return sorted(self.views_cache.keys())

    def build_view(self, viewname, tags, data, extra):
        func = self.views_cache[viewname]
        return {'result': func(data)}

    def explanation(self, data):
        """
        This just returns some text
        """
        ret = """
        <p>This is <i>just</i> some <b>example</b> text.</p>
        """
        return ret
