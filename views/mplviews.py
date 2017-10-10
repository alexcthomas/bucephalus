import uuid
import logging
import matplotlib as mpl
mpl.use('agg')
import matplotlib.pyplot as plt
import seaborn as sns
plt.ioff()

from views.baseviews import BaseViewBuilder

class MPLViewBuilder(BaseViewBuilder):
    """
    Matplotlib/seaborn views
    """
    def __init__(self):
        self.image_dir = 'img'
        self.views_cache = {
            'overview_distribution': self.overview_distribution
        }

    def list_views(self):
        return sorted(self.views_cache.keys())

    def build_view(self, viewname, tags, data, extra):
        func = self.views_cache[viewname]
        return {'result': func(data)}

    def overview_distribution(self, data):
        """
        This really needs the image size as an input
        """
        name = str(uuid.uuid1()).replace('-','')
        ret = '/'.join([self.image_dir, name+'.png'])

        key, values = list(data.items())[0]

        sns.set(style="white", palette="muted", color_codes=True)
        f, axes = plt.subplots(1, 4, figsize=(20, 5))
        sns.despine(left=True)
        sns.distplot(values, kde=False, color="b", ax=axes[0])
        sns.distplot(values, hist=False, rug=True, color="r", ax=axes[1])
        sns.distplot(values, hist=False, color="g", kde_kws={"shade": True}, ax=axes[2])
        sns.distplot(values, color="m")
        f.savefig(ret)
        logging.debug('Saved image %s', ret)
        return ret
