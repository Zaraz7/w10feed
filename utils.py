from datetime import datetime
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