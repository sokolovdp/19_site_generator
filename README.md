# Encyclopedia

Simple generator of web-site with statics pages (kind of library) to be uploaded to github.pages
Source folder 'articles' will be monitored for any changes, and then html pages will be updated accordingly

# Usage
In the current folder create subfolder 'articles' with articles to be published, then
create JSON config file config.json in the current folder with library structure description.
Run generator:
```
python site_generator.py sokolovdp.github.io
```
# Sample CONFIG.JSON file
```
{
    "topics": [
        {
            "slug": "tutorial",
            "title": "Арсенал"
        },
        {
            "slug": "python_basics",
            "title": "Основы Питона"
        },
        ...
    ],
    "articles": [
        {
            "source": "0_tutorial/14_google.md",
            "title": "Гугл",
            "topic": "tutorial"
        },
        {
            "source": "0_tutorial/27_devman.md",
            "title": "Девман",
            "topic": "tutorial"
        },
        ...
    ]
}
```
# Sample output
```
folder ./articles/ is monitored for changes
path=./articles/4_git\22_git_history.md event=modified
started site ./sokolovdp.github.io/ update process, config file: config.json
[master 8b9ccc8] commit done at 2017-06-27 13:45:38
 1 file changed, 1 insertion(+)
Branch master set up to track remote branch master from origin.
To https://github.com/sokolovdp/sokolovdp.github.io
all pages all uploaded to the site ./sokolovdp.github.io/
   7524941..8b9ccc8  master -> master
folder ./articles/ is monitored for changes
```
# Site with articles
https://sokolovdp.github.io/index.html

# Project Goals

The code is written for educational purposes. Training course for web-developers - [DEVMAN.org](https://devman.org)
  