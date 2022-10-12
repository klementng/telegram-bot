import datetime as dt
from datetime import datetime
from functools import wraps
import functools
import json
import jinja2


JINJA_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader("templates/"))

# def setup(path):
#     global JINJA_ENV
#     JINJA_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(path))
#     JINJA_ENV.filters['format_iso_time'] = format_iso_time


def format_iso_time(isoformat,format = '%Y-%m-%d %H:%M'):
    return datetime.fromisoformat(isoformat).strftime(format)
JINJA_ENV.filters['format_iso_time'] = format_iso_time


def render_response_template(path,*args,**kwargs) -> str:
    """
    Render the HMTL templates. 
    
    Also supports for 2 additional tags: <p></p> and <br> or <br/>
    
    Args:
        path: path to html file from root

    Returns:
        Fomatted html for telegram api
    
    Raises:
        jinja2.TemplateNotFound: html file not found at given path
    """

    template = JINJA_ENV.get_template(path)
    html = template.render(*args,**kwargs)
    
    html_processed = ""
    prefomatted_section = False
    for line in html.splitlines():
        
        line_stripped = line.strip()

        if line_stripped.startswith("<pre>"):
            prefomatted_section = True
        
        if prefomatted_section == True:
            if "</pre>" in line_stripped:
                prefomatted_section =False
                html_processed += line
                continue

            html_processed += line + "\n"
            continue
        
        line_stripped = line_stripped.replace('<p>',"")
        line_stripped = line_stripped.replace('</p>',"\n\n")
        line_stripped = line_stripped.replace('<br>',"\n")
        line_stripped = line_stripped.replace('<br/>',"\n")
        
        html_processed += line_stripped

    return html_processed
    


    

