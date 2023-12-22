''' Run the surver for the web-based AutoAnnotate application '''

# !/usr/bin/env python

#-----------------------------------------------------------------------
# runserver.py
#-----------------------------------------------------------------------

# import packages
import argparse
import sys
import annotate
import os

# Google expects the application to run on port 5000.
PORT = 5000

#-----------------------------------------------------------------------

def main():
    ''' 
    # Run a server for the web-based AutoAnnotate application for local testing
'''
    # parse arguments
    # desc = ['The AutoAnnotate application',
    #         'the port at which the server should listen']
    # parser = argparse.ArgumentParser(prog=sys.argv[0],
    #                                  description=desc[0])
    # parser.add_argument('port', metavar='port', type=int, help=desc[1])
    # args = parser.parse_args()
    # port = args.port
 
    try:
        annotate.app.run(host='0.0.0.0', port=PORT, debug=True,
                         ssl_context=('cert.pem', 'key.pem'))
    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

#-----------------------------------------------------------------------

if __name__ == '__main__':
    main()
