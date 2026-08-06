#!/usr/bin/env python3
import ftplib
import os
import re
from datetime import datetime
from pathlib import Path
from html.parser import HTMLParser
import argparse
import time


class FTPHandler:
    def __init__(self, host, user, password):
        self.ftp = ftplib.FTP(host, user, password)
        self.ftp.encoding = 'utf-8'
        self.ftp.sock.settimeout(5) 
    
    def list_files(self, path, pattern=""):
        # Get list with mtime
        files = []
        try:
            self.ftp.cwd(path)
            lines = []
            self.ftp.retrlines('LIST', lines.append)
            #print('list getting')
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 9 and parts[0][0] != "d":
                    filename = ' '.join(parts[8:])
                    #if filename.endswith(pattern):
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
    
    def list_filenames(self, path, pattern=""):
        return [i["name"] for i in self.list_filenames(path, pattern)]
    
    def _parse_list_time(self, line):
        """Парсит время из FTP LIST"""
        # Базовое парсирование - может отличаться в зависимости от сервера
        import time
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
            # Текущий год, время HH:MM
            hour, minute = map(int, time_or_year.split(':'))
            year = datetime.now().year
            second = 0
        else:
            # Прошлый год, только год
            year = int(time_or_year)
            hour = minute = second = 0
        
        dt = datetime(year, month, day, hour, minute, second)
        return int(dt.timestamp())
    
    def read_file(self, path):
        """Прочитать содержимое файла"""
        data = []
        try:
            self.ftp.retrbinary(f'RETR {path}', data.append)
            return b''.join(data).decode('utf-8', errors='ignore')
        except ftplib.all_errors:
            return None
    
    def close(self):
        self.ftp.quit()



# XML UTILITIES
def escape_xml(text):
    """Экранирует символы XML"""
    if text is None:
        return ''
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    return text

def format_rfc822_date(timestamp):
    """Форматирует дату в RFC 822"""
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%a, %d %b %Y %H:%M:%S +0000')

def format_iso8601_date(timestamp):
    """Форматирует дату в ISO 8601"""
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


class FeedGenerator:
    def __init__(self, config):
        self.config = config
        self.items = []
    
    def set_items(self, items):
        self.items = items
    
    def add_item(self, item):
        """Добавить элемент в ленту"""
        self.items.append(item)
    
    def generate(self):
        """Генерирует XML ленту - переопределить в подклассах"""
        raise NotImplementedError
    
    def escape(self, text):
        """Экранирует текст для XML"""
        return escape_xml(text)

class AtomGenerator(FeedGenerator):
    """Генератор Atom 1.0 ленты без использования xml модуля"""
    def generate(self):
        """Генерирует Atom ленту"""
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">')
        lines.append('<channel>')
        
        # Метаинформация о ленте
        lines.append(f'  <title>{self.escape(self.config["title"])}</title>')
        lines.append(f'  <description>{self.escape(self.config["description"])}</description>')
        lines.append(f'  <link href="{self.escape(self.config["site_url"])}" rel="alternate"/>')
        lines.append(f'  <language>{self.escape(self.config["lang"])}</language>')
        #lines.append(f'  <link href="{self.escape(self.config["output_file"])}" rel="self"/>')
        #lines.append(f'  <id>{self.escape(self.config["site_url"])}</id>')
        #lines.append(f'  <updated>{format_iso8601_date(int(time.time()))}</updated>')
        
        # Элементы
        for i, item in enumerate(self.items):
            #if self.config['debug']:
            print(f"Writing item {i+1}/{len(self.items)}: {item['title']:<70s}", end="\r")
            
            lines.append('  <item>')
            lines.append(f'    <title>{self.escape(item["title"])}</title>')
            lines.append(f'    <link>{self.escape(item["link"])}</link>')
            lines.append(f'    <guid>{self.escape(item["id"])}</guid>')
            
            # Description с поддержкой CDATA
            lines.append('    <description>')
            if self._needs_cdata(item['description']):
                lines.append(f'      <![CDATA[{item["description"]}]]>')
            else:
                lines.append(f'      {self.escape(item["description"])}')
            lines.append('    </description>')

            lines.append(f'    <pubDate>{format_iso8601_date(item["timestamp"])}</pubDate>')
            lines.append('  </item>')
        
        lines.append('</channel></rss>')
        
        
        return '\n'.join(lines)
    
    def _needs_cdata(self, text):
        return '<' in text and '>' in text

# TODO: Make class for different feed styles gen
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


def make_pics(url, host, user, passwd, title, out, maxitems):
    ftp = FTPHandler(host, user, passwd)
    PHOTOS_PATH = '/photos'
    title = title if title else f"{user} feed"
    all_images = []
    description = title
    try:
        humans = ftp.read_file('/humans.txt')
        if humans:
            description = humans.rstrip("\n")

        ftp.ftp.cwd(PHOTOS_PATH)
        lines = []
        ftp.ftp.retrlines('LIST', lines.append)
        
        img_dirs = []
        for line in lines:
            parts = line.split()
            if parts[0][0] == 'd' and parts[8][0] != '.' and len(parts) >= 9:
                dirname = ' '.join(parts[8:])
                img_dirs.append(dirname)
        
        # TODO: change "year" to "dir" or somethimg
        for year in sorted(img_dirs, reverse=True):
            year_path = f"{PHOTOS_PATH}/{year}"
            print(f"Dir: {year:<80s}")
            images = ftp.list_files(year_path, pattern=".jpg")
            #print(*images, sep="\n")

            ftp.ftp.cwd(f"{year_path}/thumbs")
            thumbs = []
            ftp.ftp.retrlines('LIST', thumbs.append)
            
            for img in images:
                # Thumbs search
                print(f"\t{img['name']:<70s}", end="\r")
                
                thumb_exists = False
                for line in thumbs:
                    if img['name'] in line:
                        thumb_exists = True
                        break
                
                thumb_url = f"{url}/photos/{year}/thumbs/{img['name']}" if thumb_exists else ""
                
                all_images.append({
                    'name': img['name'],
                    'mtime': img['mtime'],
                    'year': year,
                    'full_url': f"{url}/photos/{year}/{img['name']}",
                    'thumb_url': thumb_url
                })
    
    except ftplib.all_errors as e:
        print(f"Error with acces: {e}")
    print("Done images search")
    
    all_images.sort(key=lambda x: x['mtime'], reverse=True)
    all_images = all_images[:maxitems]

    # init RSS gen
    # TODO: Give choice to select lang
    atom_generator = AtomGenerator(config={"title":title, "description":description,\
                                           "site_url":url, "output_file":out,\
                                            "lang":"ru-RU"})

    # Making RSS items
    atom_generator.set_items(create_feed_items(all_images))
    
    with open(out, 'w', encoding='utf-8') as f:
        f.write(atom_generator.generate())


def cmd_gen(args):
    for t in args.type or 'pics':
        if t == 'pics':
            make_pics(args.url, args.host, args.user, args.passwd, args.title, args.out, args.maxitems)
        elif t == 'neocities':
            print('neocities: diz type is not ready')
        else:
            print('Bad type format, expected "pics", "neocities".')


def main():
    # cli
    argp = argparse.ArgumentParser(description='w10feed')
    sub = argp.add_subparsers(dest='cmd')
    ## Generate
    a = sub.add_parser('gen', help="Generate feed")
    a.add_argument('--type', help="Type of feed (pics, neocities)", nargs='*', required=True)
    a.add_argument('--url', help="Url for site", required=True)
    a.add_argument('--host', help="FTP host", required=True)
    a.add_argument('--user', help="FTP user")
    a.add_argument('--passwd', help="FTP user's password")
    a.add_argument('--title', help="Title of feed. Default = site domain")
    a.add_argument('--out', help="Output file of feed", default='./feed.xml')
    a.add_argument('--maxitems', help="Max items of feed", default=25)

    a.set_defaults(func=cmd_gen)

    args = argp.parse_args()
    if not hasattr(args, 'func'):
        argp.print_help()
        return
    args.func(args)


if __name__ == '__main__':
    main()