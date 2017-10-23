"""
Gunicorn config script
"""

accesslog='-'
bind = 'unix:bucephalus.sock'
workers = 1
threads = 4
worker_class = 'gevent'
worker_connections = 1000
umask = 7
user = 'nobody'
group = 'nogroup'

