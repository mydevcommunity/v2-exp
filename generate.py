# -*- coding: utf-8 -*-

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'libs'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'vendor'))

import re
import codecs
import datetime

import path
import template
import markdown

from util import truncate_html_words
from admonition import AdmonitionExtension

loader = template.Loader("_templates/")

def slugify(value, substitutions=()):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    Took from Django sources.
    """
    for src, dst in substitutions:
        value = value.replace(src.lower(), dst.lower())
    value = re.sub('[^\w\s-]', '', value).strip()
    value = re.sub('[-\s]+', '-', value)
    # we want only ASCII chars
    value = value.encode('ascii', 'ignore')
    # but Pelican should generally use only unicode
    return value.decode('ascii')

def render_page(source, template='post.html'):
    fp = codecs.open(source, mode="r", encoding="utf-8")
    md_extensions = [
        AdmonitionExtension(),
        'markdown.extensions.toc',
        'markdown.extensions.meta',
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
    ]
    md = markdown.Markdown(extensions=md_extensions)

    try:
        post_content = md.convert(fp.read())
    except Exception as e:
        print e
        print post_file
        raise

    md.body = post_content
    post_date = ''
    if 'date' in md.Meta:
        post_date = md.Meta['date'][0]
    context = {
        'post': post_content,
        'title': md.Meta['title'][0],
        'date': post_date,
    }
    return loader.load(template).generate(**context), md

def parse_date(dt_str):
    dt_fmts = (
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d %H:%M:%S',
    )
    dt = None
    for fmt in dt_fmts:
        try:
            dt = datetime.datetime.strptime(dt_str, fmt)
        except Exception as e:
            pass

    if dt is not None:
        return dt
    
    raise e

posts = []
def build_posts(text, md):
    slug = slugify(md.Meta['title'][0]).lower()
    # could be pages
    if 'date' not in md.Meta:
        return

    try:
        posts.append({
                    "date": parse_date(md.Meta['date'][0]),
                    "url": "%s.html" % slug,
                    "title": md.Meta["title"][0],
                    "body": truncate_html_words(md.body, 150),
                })
    except Exception as e:
        print e, md.Meta
        raise
    
def generate():
    for content_file in path.path('content/').walkfiles():
        if not content_file.endswith('.md'):
            continue
        content_parts = content_file.split('/')[1:]
        if len(content_parts) == 1:
            # file only, just copy
            out_path = path.path('output')
        else:
            out_path = path.path('output/%s' % '/'.join(content_parts[:-1]))

        if not out_path.exists():
            out_path.makedirs()
        
        text, md = render_page(content_file)
        slug = slugify(md.Meta['title'][0]).lower()
        out_file_path = path.path('%s/%s.html' % (out_path.relpath(), slug))
        out_file_path.write_text(text)
        build_posts(text, md)

def generate_index():
    global posts
    index_file = path.path('output/index.html')
    html = loader.load('index.html').generate(posts=posts)
    index_file.write_text(html)

assets_dir = path.path('output/assets')
if assets_dir.exists():
    assets_dir.rmtree()
assets_src = path.path('_templates/assets')
assets_src.copytree('output/assets')
generate()
posts.sort(lambda x, y: cmp(x["date"], y["date"]), reverse=True)
generate_index()
