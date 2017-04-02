import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import uuid
import os, time
plt.ioff()

class SNSViewBuilder(object):
    """
    seaborn views
    """
    def __init__(self):
        self.image_dir = 'img'

    def overview_distribution(self, data):
        """
        This really needs the image size as an input
        """
#        t0 = time.time()
        name = str(uuid.uuid1()).replace('-','')
        ret = '/'.join([self.image_dir, name+'.png'])

        sns.set(style="white", palette="muted", color_codes=True)
        f, axes = plt.subplots(1, 4, figsize=(20, 5))
        sns.despine(left=True)
        sns.distplot(data, kde=False, color="b", ax=axes[0])
        sns.distplot(data, hist=False, rug=True, color="r", ax=axes[1])
        sns.distplot(data, hist=False, color="g", kde_kws={"shade": True}, ax=axes[2])
        sns.distplot(data, color="m")
        f.savefig(ret)
#        t1 = time.time()
#        print t1-t0
        return ret



#import cStringIO
#buf = cStringIO.StringIO()
#f.savefig(buf, format='png')
#buf.seek(0)
