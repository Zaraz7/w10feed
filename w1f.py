#!/usr/bin/env python3

import argparse
import os
from version import __version__
from w10feed import make_pics, FTPHandler

def cmd_gen(args):
    ftp = FTPHandler(args.host, args.user, args.passwd)
    for t in args.type or ['pics']:
        if t == 'pics':
            make_pics(ftp, args.url, args.user, args.title, args.lang, args.out, args.maxitems)
        elif t == 'neocities':
            print(f'{t}: this type is not ready')
        elif t == 'blog':
            print(f'{t}: this type is not ready')
        else:
            print('Bad type format, expected "pics", "neocities", "blog".')
    
    if not args.local:
        ftp.ftp.cwd('/')
        if ftp.test_connection():
            print(f'Pushing {args.out} to FTP host... ', end='')
            filename = os.path.basename(args.out)
            if not ftp.upload_file(args.out, f'/{filename}'):
                print('Error')
            else:
                print('Done.')
    ftp.close()

def main():
    argp = argparse.ArgumentParser(
        description=f'w10feed {__version__} - tool for generating RSS feed for HamsterCMS sites and http://w10.host sites',
        usage='''use "%(prog)s --help" for more information
''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    argp.add_argument('-v', '--version', action='version', version=f'W10Feed {__version__}')
    sub = argp.add_subparsers(dest='cmd')
    
    # Generate command
    a = sub.add_parser('gen', help="Generate feed", formatter_class=argparse.RawTextHelpFormatter)
    a.add_argument('--type', '-t', help='''Type of feed
pics        gallery similar to https://img.triapul.cz/sect.html
blog        (WIP) /blog/* feed
neocities   (WIP) neocities.org like feed
''', nargs='+', required=True)
    a.add_argument('--url', help="URL of site")
    a.add_argument('--host', help="FTP host")
    a.add_argument('--user', "-u", help="FTP user")
    a.add_argument('--passwd', "-p", help="FTP user's password")
    a.add_argument('--title', help="Title of feed")
    a.add_argument('--out', '-o', help="Output feed file name", default='feed.xml')
    a.add_argument('--maxitems', '-m', help="Max items of feed", default=25, type=int)
    a.add_argument('--local', help="Disable upload output file back to FTP server", action='store_true')
    a.add_argument('--lang', help="Language of document", default='en-US')
    a.add_argument('--ignorecontent', help="(WIP) Don't write content of /blog/* files to feed items", action='store_true')
    a.set_defaults(func=cmd_gen)

    args = argp.parse_args()
    if not hasattr(args, 'func'):
        argp.print_help()
        return
    args.func(args)

if __name__ == '__main__':
    main()