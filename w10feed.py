#!/usr/bin/env python3
import ftplib
import os
import re
from datetime import datetime
from pathlib import Path
from html.parser import HTMLParser
import argparse


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
    
    def list_filenames(self, path, pattern=""):
        return [i["name"] for i in self.list_filenames(path, pattern)]
    
    def _parse_list_time(self, line):
        # based on ftp.w10.host server
        #import time
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
    # def push_file(self, path):
    #     try:
    #         filename = os.path.basename(path)
    #         with open(path, "rb") as file:
    #             self.ftp.storbinary(f"STOR {filename}", file)
    #         return True
    #     except:
    #         return False
    def upload_file(self, local_path, remote_path):
        """Отправить файл на FTP сервер
        
        Args:
            local_path (str): Путь к файлу на локальном компьютере
            remote_path (str): Путь назначения на FTP сервере
            
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            # Проверяем существование локального файла
            if not os.path.exists(local_path):
                print(f"Ошибка: файл {local_path} не найден")
                return False
            
            # Если remote_path содержит директорию, создаём её на сервере
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                self._ensure_remote_dir(remote_dir)
            
            self.ftp.cwd("/")
            # Открываем файл в бинарном режиме и отправляем
            with open(local_path, 'rb') as file:
                cmd = f'STOR {remote_path}'
                self.ftp.storbinary(cmd, file)
            
            print(f"✓ Файл успешно загружен: {remote_path}")
            return True
            
        except FileNotFoundError:
            print(f"Ошибка: файл {local_path} не найден")
            return False
        except ftplib.all_errors as e:
            print(f"Ошибка FTP: {e}")
            return False
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            return False

    def _ensure_remote_dir(self, remote_dir):
        """Создаёт директорию на FTP сервере, если её нет"""
        try:
            # Пытаемся перейти в директорию
            self.ftp.cwd(remote_dir)
            self.ftp.cwd('..')  # Возвращаемся обратно
        except ftplib.all_errors:
            # Директория не существует, создаём её
            try:
                self.ftp.mkd(remote_dir)
                print(f"✓ Создана директория: {remote_dir}")
            except ftplib.all_errors as e:
                print(f"Предупреждение: не удалось создать директорию {remote_dir}: {e}")
    def test_connection(self):
        """Тестирует соединение и права доступа"""
        try:
            current_dir = self.ftp.pwd()
            print(f"✓ Соединение активно")
            print(f"✓ Текущая директория: {current_dir}")
            
            # Пытаемся создать тестовый файл
            test_file = f'/test_{int(datetime.now().timestamp())}.txt'
            self.ftp.storbinary(f'STOR {test_file}', open(__file__, 'rb'))
            
            if self.ftp.size(test_file):
                self.ftp.delete(test_file)
                print(f"✓ Права доступа на запись подтверждены")
                return True
            
        except ftplib.all_errors as e:
            print(f"✗ Ошибка: {e}")
            return False
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
        self.items.append(item)
    
    def generate(self):
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
        
        # metadata
        lines.append(f'  <atom:link href="{self.escape(self.config["site_url"])}/{self.escape(self.config["output_file"])}" rel="self" type="application/rss+xml"/>')
        lines.append(f'  <title>{self.escape(self.config["title"])}</title>')
        lines.append(f'  <description>{self.escape(self.config["description"])}</description>')
        lines.append(f'  <link href="{self.escape(self.config["site_url"])}" rel="alternate"/>')
        
        # Items
        for i, item in enumerate(self.items):
            print(f"Writing item {i+1}/{len(self.items)}: {item['title']:<70s}", end="\r")
            
            lines.append('  <item>')
            lines.append(f'    <title>{self.escape(item["title"])}</title>')
            lines.append(f'    <link>{self.escape(item["link"])}</link>')
            lines.append(f'    <guid>{self.escape(item["id"])}</guid>')
            
            # Description with or without html
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


def make_pics(ftp, url, user, title, out, maxitems):
    PHOTOS_PATH = '/photos'
    title = title if title else user
    all_images = []
    description = ''
    try:
        humans = ftp.read_file('/humans.txt')
        if humans:
            description = humans.rstrip("\n")
        else:
            description = f'Site feed for {title}'

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

            #ftp.ftp.cwd(f"{year_path}/thumbs")
            # thumbs = []
            # ftp.ftp.retrlines('LIST', thumbs.append)
            
            for img in images:
                # Thumbs search
                print(f"\t{img['name']:<70s}", end="\r")
                
                #thumb_exists = False
                # for line in thumbs:
                #     if img['name'] in line:
                #         thumb_exists = True
                #         break
                
                thumb_url = f"{url}/photos/{year}/thumbs/{img['name']}"
                
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
    ftp = FTPHandler(args.host, args.user, args.passwd)
    for t in args.type or 'pics':
        if t == 'pics':
            make_pics(ftp, args.url, args.user, args.title, args.out, args.maxitems)
        elif t == 'neocities':
            print(f'{t}: diz type is not ready')
        elif t == 'blog':
            print(f'{t}: diz type is not ready')
        else:
            print('Bad type format, expected "pics", "neocities".')
    if not args.local:
        ftp.ftp.cwd('/')
        if ftp.test_connection():
            print(f'Pushing {args.out} to FTP host... ', end='')
            filename = os.path.basename(args.out)
            if not ftp.upload_file(args.out, f'/{filename}'):
                print('Error')
            print('Done.')
    ftp.close()

def main():
    # cli
    argp = argparse.ArgumentParser(description='w10feed', usage='''use "%(prog)s --help" for more information
''', formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = argp.add_subparsers(dest='cmd')
    ## Generate
    a = sub.add_parser('gen', help="Generate feed", formatter_class=argparse.RawTextHelpFormatter)
    a.add_argument('--type', '-t', help='''Type of feed
pics        gallery similar to https://img.triapul.cz/sect.html
blog        (WIP) /blog/* feed
neocities   (WIP) neocities.org like feed

''', nargs='+', required=True)
    a.add_argument('--url', help="URL of site")
    a.add_argument('--host', help="FTP host")
    a.add_argument('--user', "-n", help="FTP user")
    a.add_argument('--passwd', "-p", help="FTP user's password")
    a.add_argument('--title', help="Title of feed. Default = user")
    a.add_argument('--out', '-o', help="Output feed file name", default='feed.xml')
    a.add_argument('--maxitems', '-m', help="Max items of feed", default=25)
    a.add_argument('--local', help="Disable upload output file back to FTP server", action='store_true')
    a.add_argument('--ignorecontent', help="Don't write content of /blog/* files to feed items", action='store_true')

    a.set_defaults(func=cmd_gen)

    args = argp.parse_args()
    if not hasattr(args, 'func'):
        argp.print_help()
        return
    args.func(args)


if __name__ == '__main__':
    main()