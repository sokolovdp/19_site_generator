import sys
import os
import shutil
import json
import chardet
from datetime import datetime
import time
import subprocess
import re

import jinja2
from markdown import markdown
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONFIG_FILE = "config.json"
INDEX_FILE = "index.html"
INDEX_TEMPLATE = "index_template.html"
ARTICLE_TEMPLATE = "article_template.html"
ARTICLES_FOLDER = "./articles/"
HEADLINE_PREFIX = "## {}\n"
MONITOR_TIMEOUT = 5
CURRENT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DOMAIN_FORMAT = r"(^([a-zA-Z0-9][a-zA-Z0-9]*\.)?[a-zA-Z][a-zA-Z0-9]+\.[a-zA-Z]{1,3}$)"


def load_decoded_data(filename: str) -> str:
    with open(filename, "rb") as source_file:
        raw_data = source_file.read()
    encoding = chardet.detect(raw_data)['encoding']
    return raw_data.decode(encoding)


def load_json_data(file_name: str) -> dict:
    return json.loads(load_decoded_data(file_name))


def fetch_articles(json_catalog: dict) -> dict:
    articles = json_catalog['articles']
    topics = json_catalog['topics']
    for article_id, article_text in enumerate(articles):
        article_text['source'] = 'articles/' + article_text['source']
        article_text['id'] = article_id
    return {'articles': articles, 'topics': topics}


def render_page(html_template: str, context: dict) -> str:
    return jinja2.Environment(loader=jinja2.FileSystemLoader('./')).get_template(html_template).render(context)


def create_index_html(catalog_data: dict) -> str:
    markdown_text = ""
    for topic in catalog_data['topics']:
        head_line = HEADLINE_PREFIX.format(topic['title'])
        markdown_text = markdown_text + head_line
        for article in catalog_data['articles']:
            if article['topic'] == topic['slug']:
                article_headline = "- [{}](./{:03d}.html)\n".format(article['title'], article['id'])
                markdown_text = markdown_text + article_headline
    return markdown(markdown_text, safe_mode='escape')


def load_article_text_from_file(filename: str, title: str) -> str:
    with open(filename, encoding='utf-8') as text_file:
        markdown_text = text_file.read()
    head_line = HEADLINE_PREFIX.format(title)
    markdown_text = head_line + markdown_text
    return markdown_text


def write_html_page_to_file(filename: str, html_text: str):
    with open(file=filename, mode='w', encoding='utf-8') as html_file:
        html_file.write(html_text)


def clean_site_directory(dir_name: str):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    else:
        shutil.rmtree(dir_name, ignore_errors=True)
        os.makedirs(dir_name)


def current_date_time() -> str:
    return datetime.fromtimestamp(time.time()).strftime(CURRENT_DATE_FORMAT)


def push_site_to_github(site_dir):
    current_directory = os.getcwd()
    os.chdir(site_dir)
    subprocess.call(['git', 'add', '--all'])
    subprocess.call(['git', 'commit', '-m', 'commit done at {}'.format(current_date_time())])
    subprocess.call(['git', 'push', '-u', 'origin master'])
    os.chdir(current_directory)


def prepare_and_upload_site_to_github(config: str, site_directory: str):
    print("started text update for site {}, config file: {}".format(site_directory, config))

    json_data = load_json_data(config)
    index = fetch_articles(json_data)

    index_html = create_index_html(index)
    index_context = dict(index_html=index_html)
    index_html_page = render_page(INDEX_TEMPLATE, index_context)
    write_html_page_to_file(os.path.join(site_directory, INDEX_FILE), index_html_page)

    for article in index['articles']:
        article_text = load_article_text_from_file(article['source'], article['title'])
        article_html = markdown(article_text, safe_mode='escape')
        article_context = dict(article_html=article_html)
        article_html_page = render_page(ARTICLE_TEMPLATE, article_context)
        article_file = "{:03d}.html".format(article['id'])
        write_html_page_to_file(os.path.join(site_directory, article_file), article_html_page)

    push_site_to_github(site_directory)
    print("all pages all uploaded to the site {}".format(site_directory))


class DirEventsHandler(FileSystemEventHandler):
    def __init__(self, folder=None):
        if folder is not None:
            self.folder = folder
        else:
            print("DirEventsHandler initialization error: no domain folder name")

    def on_any_event(self, event):
        print("path={} event={} site_folder={}".format(event.src_path, event.event_type, self.folder))
        if not event.is_directory:
            prepare_and_upload_site_to_github(CONFIG_FILE, self.folder)
            print("folder {} is monitored for changes".format(ARTICLES_FOLDER))


def is_domain_name_valid(string: str) -> bool:
    match = re.search(DOMAIN_FORMAT, string)
    return True if match else False


if __name__ == "__main__":
    domain_name = sys.argv[1]
    if not is_domain_name_valid(domain_name):
        print("invalid domain name format {}".format(domain_name))
    else:
        site_folder_name = os.path.join(os.getcwd(), domain_name)
        clean_site_directory(site_folder_name)
        prepare_and_upload_site_to_github(CONFIG_FILE, site_folder_name)
        observer = Observer()
        observer.schedule(DirEventsHandler(folder=site_folder_name), ARTICLES_FOLDER, recursive=True)
        observer.start()
        print("domain folder {} is monitored for changes".format(ARTICLES_FOLDER))
        try:
            while True:
                time.sleep(MONITOR_TIMEOUT)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
