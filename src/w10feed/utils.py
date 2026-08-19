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
def replace_relative_urls(html, cms_url_placeholder="{cms_url}"):
    """
    Заменяет относительные пути в href и src на {cms_url}...
    Игнорирует:
    - Абсолютные пути с протоколом (http://, https://, gopher://, и т.д.)
    - Пути начинающиеся с // (protocol-relative)
    - Якори (#fragment)
    - Содержимое внутри <pre> и других тегов с кодом
    """
    
    # Регулярное выражение для href и src атрибутов
    # Захватывает:
    # - Группа 1: открывающая кавычка (" или ')
    # - Группа 2: атрибут (href или src)
    # - Группа 3: закрывающая кавычка (совпадает с открывающей)
    # - Группа 4: значение пути
    
    # Основной regex для href и src
    # (?:href|src)=(["\'])([^"\']*)\1
    # Но нужно учитывать, что кавычка может быть разной
    
    #pattern = r'(href|src)=(["\'])([^\2]*?)\2'
    
    # Более надёжный вариант с именованными группами:
    #pattern = r'(href|src)=([\"\'])(?:(?=(\\?))\3.)*?\2'
    
    # Самый простой и работающий вариант:
    pattern = r'(href|src)=(["\'])([^"\']*)\2'
    
    def replace_url(match):
        attr_name = match.group(1)
        quote = match.group(2)
        url = match.group(3)
        
        # Проверка на относительный путь
        if (not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', url) and
            not url.startswith('//') and
            not url.startswith('#')):
            return f'{attr_name}={quote}{cms_url_placeholder}{url}{quote}'
        
        return match.group(0)
    
    return re.sub(pattern, replace_url, html)