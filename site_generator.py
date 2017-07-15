# System modules
import sys
import os
import json
import chardet
from datetime import datetime
import time
import subprocess
# Application modules
from markdown import markdown
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import jinja2

# Global constants
CONFIG_FILE = 'config.json'
INDEX_FILE = 'index.html'
INDEX_TEMPLATE = 'index_template.html'
ARTICLE_TEMPLATE = 'article_template.html'
ARTICLES_FOLDER = "./articles/"

# Global vars
site_folder_name = ""


def load_decoded_data(filename: "str") -> "str":
    with open(filename, "rb") as file:
        raw_data = file.read()
    encoding = chardet.detect(raw_data)['encoding']
    return raw_data.decode(encoding)


def load_json_data(file_name: "str") -> "dict":
    return json.loads(load_decoded_data(file_name))


def fetch_articles(json_catalog: "dict") -> "dict":
    articles = json_catalog['articles']
    topics = json_catalog['topics']
    for article_id, article_text in enumerate(articles):
        article_text['source'] = 'articles/' + article_text['source']
        article_text['id'] = article_id
    return {'articles': articles, 'topics': topics}


def render_page(html_template: "str", context: "dict") -> "str":
    return jinja2.Environment(loader=jinja2.FileSystemLoader('./')).get_template(html_template).render(context)


def create_index_html(catalog_data: "dict") -> "str":
    md_text = ''
    for topic in catalog_data['topics']:
        head_line = "## {}\n".format(topic['title'])
        md_text = md_text + head_line
        for article in catalog_data['articles']:
            if article['topic'] == topic['slug']:
                art_line = "- [{}](./{:03d}.html)\n".format(article['title'], article['id'])
                md_text = md_text + art_line
    return markdown(md_text, safe_mode='escape')


def load_article_text(filename: "str", title: "str") -> "str":
    with open(filename, encoding='utf-8') as f_text:
        md_text = f_text.read()
    md_text = "##{}\n{}".format(title, md_text)  # add title to article text
    return md_text


def write_html_page(filename: "str", html_text: "str"):
    with open(file=filename, mode='w', encoding='utf-8') as f:
        f.write(html_text)


def clean_site_directory(dir_name: "str"):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    else:
        for file in os.listdir(dir_name):
            file_path = os.path.join(dir_name, file)
            if os.path.isfile(file_path):  # delete file
                os.unlink(file_path)


def current_date_time() -> "str":
    return datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')


def push_site_to_github(site_dir):
    current_directory = os.getcwd()
    os.chdir(site_dir)
    subprocess.call(['git', 'add', '--all'])
    subprocess.call(['git', 'commit', '-m', 'commit done at {}'.format(current_date_time())])
    subprocess.call(['git', 'push', '-u', 'origin master'])
    os.chdir(current_directory)


def prepare_and_upload_site_to_github(config: "str", site_directory: "str"):
    print("started text update for site {}, config file: {}".format(site_directory, config))

    clean_site_directory(site_directory)

    json_data = load_json_data(config)
    index = fetch_articles(json_data)

    index_html = create_index_html(index)
    index_context = dict(index_html=index_html)
    index_html_page = render_page(INDEX_TEMPLATE, index_context)
    write_html_page(site_directory + INDEX_FILE, index_html_page)

    for article in index['articles']:
        article_text = load_article_text(article['source'], article['title'])
        article_html = markdown(article_text, safe_mode='escape')
        article_context = dict(article_html=article_html)
        article_html_page = render_page(ARTICLE_TEMPLATE, article_context)
        article_file = "{:03d}.html".format(article['id'])
        write_html_page(site_directory + article_file, article_html_page)

    push_site_to_github(site_directory)
    print("all pages all uploaded to the site {}".format(site_directory))


class MyHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        print("path={} event={}".format(event.src_path, event.event_type))
        if event.is_directory:
            return None
        prepare_and_upload_site_to_github(CONFIG_FILE, site_folder_name)
        print("folder {} is monitored for changes".format(ARTICLES_FOLDER))


if __name__ == "__main__":

    site_url = sys.argv[1]
    site_folder_name = "./" + site_url + "/"

    prepare_and_upload_site_to_github(CONFIG_FILE, site_folder_name)
    observer = Observer()
    observer.schedule(MyHandler(), ARTICLES_FOLDER, recursive=True)
    observer.start()
    print("folder {} is monitored for changes".format(ARTICLES_FOLDER))
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
