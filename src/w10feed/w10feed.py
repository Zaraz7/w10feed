#!/usr/bin/env python3

import os
from .utils import *
from .version import __version__
from xml.dom import minidom

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
    def generate(self):
        doc = minidom.Document()
        
        rss = doc.createElement('rss')
        rss.setAttribute('version', '2.0')
        rss.setAttribute('xmlns:atom', 'http://www.w3.org/2005/Atom')
        doc.appendChild(rss)
        
        channel = doc.createElement('channel')
        rss.appendChild(channel)
        
        # Metadata
        atom_link = doc.createElement('atom:link')
        atom_link.setAttribute('href', f"{self.config['site_url']}/{self.config['output_file']}")
        atom_link.setAttribute('rel', 'self')
        atom_link.setAttribute('type', 'application/rss+xml')
        channel.appendChild(atom_link)
        
        self._add_text_element(doc, channel, 'title', self.config['title'])
        self._add_text_element(doc, channel, 'description', self.config['description'])
        self._add_text_element(doc, channel, 'link', self.config['site_url'])
        self._add_text_element(doc, channel, 'language', self.config['lang'])
        self._add_text_element(doc, channel, 'lastBuildDate', format_rfc822_date(datetime.now().timestamp()))
        self._add_text_element(doc, channel, 'generator', f'w10feed/{__version__}')
        
        # Items
        for i, item in enumerate(self.items):
            print(f"Writing item {i+1}/{len(self.items)}: {item['title']:<70s}", end="\r")
            
            item_elem = doc.createElement('item')
            channel.appendChild(item_elem)
            
            self._add_text_element(doc, item_elem, 'title', item['title'])
            
            uri = iri_to_uri(self.escape(item['link']))
            self._add_text_element(doc, item_elem, 'link', uri)
            self._add_text_element(doc, item_elem, 'guid', uri)
            
            # Description with proper CDATA handling
            if item['description'] != '':
                desc_elem = doc.createElement('description')
                item_elem.appendChild(desc_elem)
                
                if self._needs_cdata(item['description']):
                    cdata = doc.createCDATASection(item['description'])
                    desc_elem.appendChild(cdata)
                else:
                    text_node = doc.createTextNode(item['description'])
                    desc_elem.appendChild(text_node)
            
            self._add_text_element(doc, item_elem, 'pubDate', format_rfc822_date(item['timestamp']))
        
        xml_str = doc.toxml(encoding='UTF-8').decode('UTF-8')

        return xml_str
    
    def _add_text_element(self, doc, parent, tag_name, text):
        elem = doc.createElement(tag_name)
        text_node = doc.createTextNode(self.escape(text))
        elem.appendChild(text_node)
        parent.appendChild(elem)
    
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

            description = replace_relative_urls(description, f'{site_url}/cgi-bin/cms/')

        
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
        
    except handler.ERRORS as e:
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
    except handler.ERRORS as e:
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