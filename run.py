# -*- coding: utf-8 -*-
"""
Created on Wed Oct 11 15:31:58 2017

@author: alex
"""

import argparse

from bucephalus import app

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bucephalus',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--port', type=int, default=5000,
        help="Web port")
    parser.add_argument('--host', type=str, default="0.0.0.0",
        help="IP address to listen on")
    params = parser.parse_args()

    app.run(host=params.host, port=params.port, threaded=True, debug=True, use_debugger=False, use_reloader=False)