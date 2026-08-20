#!/usr/bin/env python3
import argparse
import os
import sys
import getpass
from src.w10feed.w10feed import make_pics, make_blog, FTPHandler, __version__

try:
    from config import PROFILES
except ImportError:
    PROFILES = {}

def get_password(prompt="Enter FTP password: "):
    try:
        return getpass.getpass(prompt)
    except (KeyboardInterrupt, EOFError):
        print("\nPassword input cancelled")
        sys.exit(1)

def merge_config(profile_config, cli_args):
    args = vars(cli_args)
    merged_config = profile_config.copy()
    for key, value in args.items():
        if value != None:
            merged_config[key] = value
    return merged_config

# I think this sh1t I need 2 move in w10feed.py
def run_profile(profile_name, args=None):
    if profile_name not in PROFILES:
        print(f"Error: Profile '{profile_name}' not found in config.py")
        print(f"Available profiles: {', '.join(PROFILES.keys())}")
        return False
    
    profile_config = PROFILES[profile_name]
    
    if profile_config.get('passwd', '') == '' and (not args or not args.passwd):
        password = get_password(f"Enter password for profile '{profile_name}': ")
        profile_config = profile_config.copy()
        profile_config['passwd'] = password
    
    config = merge_config(profile_config, args)
    
    types = config['type']
    if isinstance(types, str):
        types = [types]
    elif not isinstance(types, list):
        types = []
    
    handler = FTPHandler(config['host'], config['user'], config['passwd'])
    
    for t in types:
        if t == 'pics':
            make_pics(
                handler, config['url'], config['user'], config['title'],
                config['lang'], config['out'], config['maxitems']
            )
        elif t == 'blog':
            make_blog(
                handler, config['url'], config['user'], config['title'],
                config['lang'], config['out'], config['maxitems'],
                config.get('sort', 'mtime'), config.get('no_description', False)
            )
        elif t == 'neocities':
            print(f'{t}: This type is not ready yet')
        else:
            print(f'Bad type format: {t}. Expected "pics", "blog", "neocities"')
    
    if not config.get('local', False):
        if handler.test_connection():
            print(f'Pushing {config["out"]} to FTP host... ', end='')
            filename = os.path.basename(config['out'])
            if not handler.upload_file(config['out'], f'/{filename}'):
                print('Error')
            else:
                print('Done.')
    
    handler.close()
    return True

def cmd_gen(args):
    if not args.passwd:
        args.passwd = get_password("Enter FTP password: ")

    handler = FTPHandler(args.host, args.user, args.passwd)
    
    for t in args.type:
        if t == 'pics':
            make_pics(handler, args.url, args.user, args.title, args.lang, args.out, args.maxitems)
        elif t == 'blog':
            make_blog(handler, args.url, args.user, args.title, args.lang, args.out, 
                     args.maxitems, args.sort, args.no_description)
        elif t == 'neocities':
            print(f'{t}: Diz type is not ready')
        else:
            print(f'Bad type format: {t}. Expected "pics", "blog", "neocities"')
    
    if not args.local:
        if handler.test_connection():
            print(f'Pushing {args.out} to FTP host... ', end='')
            filename = os.path.basename(args.out)
            if not handler.upload_file(args.out, f'/{filename}'):
                print('Error')
            else:
                print('Done.')
    handler.close()

def cmd_profile(args):
    if not PROFILES:
        print("Error: No profiles defined in config.py")
        print("Please create a config.py file with PROFILES dictionary")
        return
    
    if args.profile == 'all':
        # Run all profiles
        success = True
        for profile_name in PROFILES:
            print(f"Running profile: {profile_name}")
            print(f"{'='*60}")
            if not run_profile(profile_name, args):
                success = False
        if success:
            print("All profiles completed successfully.")
        else:
            print("Some profiles failed.")
    else:
        if args.profile is None:
            profile_name = list(PROFILES.keys())[0]
            print(f"No profile specified, using first profile: {profile_name}")
        else:
            profile_name = args.profile
        run_profile(profile_name, args)

def main():
    argp = argparse.ArgumentParser(
        description=f'w10feed {__version__} - tool for generating RSS feed for HamsterCMS sites and http://w10.host sites',
        usage='''use "%(prog)s --help" for more information
''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    argp.add_argument('-v', '--version', action='version', version=f'%(prog)s {__version__}')
    sub = argp.add_subparsers(dest='cmd')
    
    # Generate command
    a = sub.add_parser('gen', help="Generate feed", formatter_class=argparse.RawTextHelpFormatter)
    a.add_argument('--type', '-t', help='''Type of feed
pics        gallery similar to https://img.triapul.cz/sect.html
blog        /blog/*.txt feed
neocities   (WIP) neocities.org like feed
''', nargs='+', required=True)
    a.add_argument('--url', help="URL of site", required=True)
    a.add_argument('--host', help="FTP host", required=True)
    a.add_argument('--user', "-u", help="FTP user", required=True)
    a.add_argument('--passwd', "-p", help="FTP user's password")
    a.add_argument('--title', help="Title of feed")
    a.add_argument('--out', '-o', help="Output feed file name", default='feed.xml')
    a.add_argument('--maxitems', '-m', help="Max items of feed", default=25, type=int)
    a.add_argument('--local', help="Disable upload output file back to FTP server", action='store_true')
    a.add_argument('--lang', help="Language of document", default='en-US')
    #p.add_argument('--save', help="(WIP) Don't remove local temporary output file", action='store_true')
    # Blog-specific options
    a.add_argument('--sort', help='Sort blog posts by: mtime (modification time) or name', 
                  choices=['mtime', 'name'], default='mtime')
    a.add_argument('--no-description', help="Generate feed without descriptions (only titles and links)", 
                  action='store_true')
    
    a.set_defaults(func=cmd_gen)

    p = sub.add_parser('profile', help='Run profile from config.py', 
                       formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument('profile', nargs='?', help='''Profile name from config.py
Use 'all' to run all profiles
If not specified, runs the first profile''')
    p.add_argument('--passwd', "-p", help="FTP password (overrides config)")
    p.add_argument('--local', help="Disable upload output file back to FTP server", 
                   action='store_true')
    #p.add_argument('--save', help="(WIP) Don't remove local temporary output file", action='store_true')
    p.set_defaults(func=cmd_profile)

    args = argp.parse_args()
    if not hasattr(args, 'func'):
        argp.print_help()
        return
    args.func(args)

if __name__ == '__main__':
    main()