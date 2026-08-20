from datetime import datetime
import re
from urllib.parse import quote, urlparse, urlunparse

def iri_to_uri(iri):
    parts = urlparse(iri)
    try:
        netloc = parts.netloc.encode('idna').decode('ascii')
    except (UnicodeError, UnicodeDecodeError):
        netloc = parts.netloc
    
    return urlunparse((
        parts.scheme,
        netloc,
        quote(parts.path, safe='/', encoding='utf-8'),
        quote(parts.params, safe='', encoding='utf-8'),
        quote(parts.query, safe='=&', encoding='utf-8'),
        quote(parts.fragment, safe='', encoding='utf-8')
    ))

# XML UTILITIES
def escape_xml(text):
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
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%a, %d %b %Y %H:%M:%S +0300') # временное решение. Необходимо добавить опцию для разных часовых поясов

def format_iso8601_date(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

# HTML Utils
def replace_relative_urls(html, url_placeholder):
    """
    Replace links in href and src
    Inore:
    - absolute urls w (http://, https://, gopher://, и т.д.)
    - protocol-relative
    - anchors
    """
    pattern = r'(<[^>]*(href|src)=)(["\'])([^"\']*)\3'
    
    def replace_url(match):
        tag_part = match.group(1)  # <a href=
        quote = match.group(3)      # "
        url = match.group(4) 
        
        if (not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', url) and
            not url.startswith('//') and
            not url.startswith('#')):
            return f'{tag_part}{quote}{url_placeholder}{url}{quote}'
        
        return match.group(0)
    
    return re.sub(pattern, replace_url, html)