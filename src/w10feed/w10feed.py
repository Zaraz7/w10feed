#!/usr/bin/env python3
import ftplib
import os
import re
from .utils import *
from .version import __version__

class FTPHandler:
    def __init__(self, host, user, password):
        self.ftp = ftplib.FTP(host, user, password)
        self.ftp.encoding = 'utf-8'
        self.ftp.sock.settimeout(15)
    def cd(self, path):
        self.ftp.cwd(path)

    def list_files(self, path, pattern=""):
        files = []
        try:
            self.ftp.cwd(path)
            lines = []
            self.ftp.retrlines('LIST', lines.append)
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 9 and parts[0][0] != "d":
                    filename = ' '.join(parts[8:])
                    if filename.endswith(pattern):
                        # MMM DD HH:MM or MMM DD YYYY
                        try:
                            mtime = self._parse_list_time(line)
                            files.append({
                                'name': filename,
                                'mtime': mtime,
                                'path': f"{path}/{filename}"
                            })
                        except:
                            pass
        except ftplib.all_errors:
            pass
        return sorted(files, key=lambda x: x['mtime'], reverse=True)
    
    def list_dirs(self, path):
        """Get list of directories in path"""
        dirs = []
        try:
            self.ftp.cwd(path)
            lines = []
            self.ftp.retrlines('LIST', lines.append)
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 9 and parts[0][0] == 'd' and parts[8][0] != '.':
                    dirname = ' '.join(parts[8:])
                    dirs.append(dirname)
        except ftplib.all_errors:
            pass
        return dirs
    
    def _parse_list_time(self, line):
        # based on ftp.w10.host server
        parts = line.split()
        month_str = parts[5]
        day = parts[6]
        time_or_year = parts[7]
        
        months = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        month = months.get(month_str, 1)
        day = int(day)
        
        if ':' in time_or_year:
            # This year
            hour, minute = map(int, time_or_year.split(':'))
            year = datetime.now().year
            second = 0
        else:
            # prevew year
            year = int(time_or_year)
            hour = minute = second = 0
        
        dt = datetime(year, month, day, hour, minute, second)
        return int(dt.timestamp())
    
    def read_file(self, path):
        data = []
        try:
            self.ftp.retrbinary(f'RETR {path}', data.append)
            return b''.join(data).decode('utf-8', errors='ignore')
        except ftplib.all_errors:
            return None

    def upload_file(self, local_path, remote_path):
        try:
            if not os.path.exists(local_path):
                print(f"Error: local {local_path} not found")
                return False
            
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                self._ensure_remote_dir(remote_dir)
            
            self.ftp.cwd(remote_dir)
            with open(local_path, 'rb') as file:
                cmd = f'STOR {remote_path}'
                self.ftp.storbinary(cmd, file)
            
            print(f"File uploaded: {remote_path}")
            return True
            
        except FileNotFoundError:
            print(f"Error: file {local_path} not found")
            return False
        except ftplib.all_errors as e:
            print(f"FTP error: {e}")
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False

    def _ensure_remote_dir(self, remote_dir):
        try:
            self.ftp.cwd(remote_dir)
            self.ftp.cwd('..')
        except ftplib.all_errors:
            # creating a missing directory
            try:
                self.ftp.mkd(remote_dir)
            except ftplib.all_errors as e:
                print(f"Warning: {remote_dir} doesn't create: {e}")
    
    def test_connection(self, debug=False):
        try:
            current_dir = self.ftp.pwd()
            if debug:
                print("Connection active.")
                print(f"PWD: {current_dir}")
            
            # Trying make test file
            test_file = f'/test_{int(datetime.now().timestamp())}.txt'
            self.ftp.storbinary(f'STOR {test_file}', open(__file__, 'rb'))
            
            if self.ftp.size(test_file):
                self.ftp.delete(test_file)
                if debug:
                    print(f"Write access rights confirmed.")
                return True
            
        except ftplib.all_errors as e:
            print(f"Error: {e}")
            return False
    
    def close(self):
        self.ftp.quit()

class FeedGenerator:
    def __init__(self, config):
        self.config = config
        self.items = []
    
    def set_items(self, items):
        self.items = items
    
    def add_item(self, item):
        self.items.append(item)
    
    def generate(self):
        raise NotImplementedError
    
    def escape(self, text):
        return escape_xml(text)

class RSSGenerator(FeedGenerator):
    # RSS 2.0 generator without xml mobule because i fucked built-in escaping  
    def generate(self):
        # TODO: Maybe need own xml builder
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">')
        lines.append('<channel>')
        
        # metadata
        lines.append(f'  <atom:link href="{self.escape(self.config["site_url"])}/{self.escape(self.config["output_file"])}" rel="self" type="application/rss+xml"/>')
        lines.append(f'  <title>{self.escape(self.config["title"])}</title>')
        lines.append(f'  <description>{self.escape(self.config["description"])}</description>')
        lines.append(f'  <link>{self.escape(self.config["site_url"])}</link>')
        lines.append(f'  <language>{self.escape(self.config["lang"])}</language>')
        lines.append(f'  <lastBuildDate>{format_rfc822_date(datetime.now().timestamp())}</lastBuildDate>')
        lines.append(f'  <generator>w10feed/{__version__}</generator>')
        
        # Items
        for i, item in enumerate(self.items):
            print(f"Writing item {i+1}/{len(self.items)}: {item['title']:<70s}", end="\r")
            
            lines.append('  <item>')
            lines.append(f'    <title>{self.escape(item["title"])}</title>')
            uri = iri_to_uri(self.escape(item["link"]))
            lines.append(f'    <link>{uri}</link>')
            lines.append(f'    <guid>{uri}</guid>')
            
            # Description with or without html
            if item['description'] != '':
                lines.append('    <description>')
                if self._needs_cdata(item['description']):
                    lines.append(f'      <![CDATA[{item["description"]}]]>')
                else:
                    lines.append(f'      {self.escape(item["description"])}')
                lines.append('    </description>')

            lines.append(f'    <pubDate>{format_rfc822_date(item["timestamp"])}</pubDate>')
            lines.append('  </item>')
        
        lines.append('</channel></rss>')
        return '\n'.join(lines)
    
    def _needs_cdata(self, text):
        return '<' in text and '>' in text

# Wow, this is still peace of shi
def create_feed_items(images):
    items = []
    for i, img in enumerate(images):
        print(f"Creating item {i+1}/{len(images)}: {img['name']:<70s}", end="\r")
        
        title = img['name']
        for ext in ['.jpg', '.jpeg', '.png', '.gif']:
            title = title.replace(ext, '')
        
        # Default image description like https://img.triapul.cz/sect.html
        desc_html = f'<p><img class="webring" src="{img["full_url"]}" data-timestamp="{img["mtime"]}" data-thumb="{img["thumb_url"]}" alt="{title}"></p>'
        desc_html += f'<p><a href="{img["full_url"]}">full size</a></p>'
        
        item = {
            'title': title,
            'link': img['full_url'],
            'id': img['full_url'],
            'timestamp': img['mtime'],
            'description': desc_html
        }
        items.append(item)
    return items

def create_blog_items(blog_posts, site_url, no_description=False):
    items = []
    for i, post in enumerate(blog_posts):
        print(f"Creating item {i+1}/{len(blog_posts)}: {post['name']:<70s}", end="\r")
        
        # Extract title from first <h3> or use filename
        content = post['content']
        title_match = re.search(r'<h3[^>]*>(.*?)</h3>', content, re.IGNORECASE | re.DOTALL)
        
        if title_match:
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
        else:
            title = post['name'].replace('.txt', '').replace('_', ' ').title()
            
        
        # If no_description flag is True, use empty description
        description = ''
        if not no_description:
            if title_match:
                # Remove first <h3> from description
                description = re.sub(r'<h3[^>]*>.*?</h3>', '', content, count=1, flags=re.IGNORECASE | re.DOTALL)
            else:
                description = content
            # replace relative path to absolute
            description = re.sub(
                r'href=(["\'])([^/][^"\']*)',
                rf'href=\1{site_url}/cgi-bin/cms/\2',
                description
            )
            description = re.sub(
                r'=(["\'])\.\.\/\.\.\/',
                rf'=\1{site_url}/',
                description
            )

        
        item = {
            'title': title,
            'link': f"{site_url}/blog/{post['name']}",
            'id': f"{site_url}/blog/{post['name']}",
            'timestamp': post['mtime'],
            'description': description
        }
        items.append(item)
    return items

def make_blog(handler, url, user, title, lang, out, maxitems, sort_by='mtime', no_description=False):
    BLOG_PATH = '/blog'
    title = title if title else f"{user}'s Blog"
    
    try:
        # Read humans.txt for description
        humans = handler.read_file('/humans.txt')
        description = humans.rstrip("\n") if humans else f'Blog feed for {title}'
        
        # Get list of .txt files in /blog
        blog_files = handler.list_files(BLOG_PATH, pattern=".txt")
        
        if not blog_files:
            print("No blog posts found in /blog directory")
            return
        
        print(f"Found {len(blog_files)} blog posts")
        
        # Read content of each blog post
        blog_posts = []
        for file_info in blog_files:
            content = handler.read_file(f"{BLOG_PATH}/{file_info['name']}")
            if content:
                blog_posts.append({
                    'name': file_info['name'],
                    'mtime': file_info['mtime'],
                    'content': content
                })
        
        # Sort posts
        if sort_by == 'name':
            blog_posts.sort(key=lambda x: x['name'], reverse=True)
        else:  # sort by mtime (default)
            blog_posts.sort(key=lambda x: x['mtime'], reverse=True)
        
        # Limit items
        blog_posts = blog_posts[:maxitems]
        
        # Generate RSS
        rss_generator = RSSGenerator(config={
            "title": title,
            "description": description,
            "site_url": url,
            "output_file": out,
            "lang": lang
        })
        
        rss_generator.set_items(create_blog_items(blog_posts, url, no_description))
        
        with open(out, 'w', encoding='utf-8') as f:
            f.write(rss_generator.generate())
        
        print(f"\nBlog feed generated: {out}")
        
    except ftplib.all_errors as e:
        print(f"Error accessing FTP: {e}")

def make_pics(handler, url, user, title, lang, out, maxitems):
    PHOTOS_PATH = '/photos'
    title = title if title else user
    all_images = []
    

    humans = handler.read_file('/humans.txt')
    description = humans.rstrip("\n") if humans else f'Site feed for {title}'

    img_dirs = handler.list_dirs(PHOTOS_PATH)
    try:
        # TODO: change "year" to "dir" or somethimg
        for year in sorted(img_dirs, reverse=True):
            year_path = f"{PHOTOS_PATH}/{year}"
            print(f"Dir: {year:<80s}")
            images = handler.list_files(year_path, pattern=".jpg")
            
            for img in images:
                print(f"\t{img['name']:<70s}", end="\r")
                
                thumb_url = f"{url}/photos/{year}/thumbs/{img['name']}"
                
                all_images.append({
                    'name': img['name'],
                    'mtime': img['mtime'],
                    'year': year,
                    'full_url': f"{url}/photos/{year}/{img['name']}",
                    'thumb_url': thumb_url
                })
    except ftplib.all_errors as e:
        print(f"Error accessing FTP: {e}")

    print("Done images search")
    
    all_images.sort(key=lambda x: x['mtime'], reverse=True)
    all_images = all_images[:maxitems]

    rss_generator = RSSGenerator(config={
        "title": title,
        "description": description,
        "site_url": url,
        "output_file": out,
        "lang": lang
    })

    rss_generator.set_items(create_feed_items(all_images))
    
    with open(out, 'w', encoding='utf-8') as f:
        f.write(rss_generator.generate())