import jinja2
import json
import chardet
import os
from markdown import markdown
import subprocess
import datetime
import time

config_file = 'config.json'
index_file = 'index.html'
index_template = 'index_template.html'
article_template = 'article_template.html'
site_folder_name = "sokolovdp.github.io"


def load_decoded_data(filename: "str") -> "str":
    with open(filename, "rb") as file:
        raw_data = file.read()
    encoding = chardet.detect(raw_data)['encoding']
    return raw_data.decode(encoding)


def load_json_data(filename: "str") -> "dict":
    try:
        return json.loads(load_decoded_data(filename))
    except json.decoder.JSONDecodeError:
        print("file {} contains invalid json data, load aborted!".format(filename))


def fetch_articles(json_catalog: "dict") -> "dict":
    articles = json_catalog['articles']
    topics = json_catalog['topics']
    for aid, article in enumerate(articles):
        article['source'] = 'articles/' + article['source']
        article['id'] = aid
    return {'articles': articles, 'topics': topics}


def render(html_template: "str", context: "dict") -> "str":
    return jinja2.Environment(loader=jinja2.FileSystemLoader('./')).get_template(html_template).render(context)


def create_index_html(catalog_data: "dict") -> "str":
    md_text = ''
    for topic in catalog_data['topics']:
        head_line = f"## {topic['title']}\n"
        md_text = f"{md_text}{head_line}"
        for article in catalog_data['articles']:
            if article['topic'] == topic['slug']:
                art_line = f"- [{article['title']}](./{article['id']:03d}.html)\n"
                md_text = f"{md_text}{art_line}"
    return markdown(md_text, safe_mode='escape')


def load_article_text(filename: "str", title: "str") -> "str":
    with open(filename, encoding='utf-8') as f_text:
        md_text = f_text.read()
    md_text = f"##{title}\n{md_text}"  # add title to article text
    return md_text


def write_html_page(filename: "str", html_text: "str"):
    with open(file=filename, mode='w', encoding='utf-8') as f:
        f.write(html_text)


def clean_output_directory(dir_name: "str") -> "bool":
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    else:
        for file in os.listdir(dir_name):
            file_path = os.path.join(dir_name, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    # elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except OSError:
                print("access error: file {} is used by another process".format(file_path))
                return False
            except Exception as e:
                print(e)
                return False
    return True


def current_date_time() -> "str":
    return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')


def push_site_to_github(site_dir):
    current_directory = os.getcwd()
    os.chdir(site_dir)
    subprocess.call('git add --all')
    subprocess.call(f'git commit -m "commit done at {current_date_time()}"')
    subprocess.call('git push -u origin master')
    os.chdir(current_directory)
    return True


def main(config: "str", site_directory: "str"):
    json_data = load_json_data(config)
    index = fetch_articles(json_data)

    index_html = create_index_html(index)
    index_context = {'index_html': index_html}
    index_html_page = render(index_template, index_context)
    write_html_page(f"{site_directory}{index_file}", index_html_page)

    for article in index['articles']:
        article_text = load_article_text(article['source'], article['title'])
        article_html = markdown(article_text, safe_mode='escape')
        article_context = {'article_html': article_html}
        article_html_page = render(article_template, article_context)
        article_file = f"{article['id']:03d}.html"
        write_html_page(f"{site_directory}{article_file}", article_html_page)

    push_site_to_github(site_directory)


if __name__ == "__main__":
    if clean_output_directory(site_folder_name):
        main(config_file, f"./{site_folder_name}/")
