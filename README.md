# w10feed
<!-- TODO: надо бы добавить описание на русском -->
<!-- "sorry for my bed england" -->
RSS 2.0 generator for [HamsterCMS](http://hamster.oldcities.org) sites and [Web1.0 Hosting](http://w10.host) sites

The website's file system must be accessible via FTP. _No additional packages need_ to be installed. The program uses built-in or custom-written modules. 

## Feachers
- Custom title, language, max items, filename
- Description for feed is takes from /humans.txt. Like in w10.host's "Last edited | Most visited | Most liked" list
- The intermediate generation file remains in the program's startup directory, allowing for on-site verification.
- You can configure different profiles. More details in the `config.py`.
- The following tape options are available:

### Ocular Webring like feed
I did this primarily for myself, because I wanted to join the party of [subversive.pics](https://img.triapul.cz/sect.html) or [Ocular Webring](https://codeberg.org/rostiger/ocular_webring).
It is generates a news feed with .jpg pictures based on your site's `/photos` directory.

[Example](https://zaraz7.narod.ws/img.xml):

```bash
python3 w1f.py gen --type pics --url "https://zaraz7.narod.ws" --host ftp.narod.ws --title "Галерея Zaraz7" -o img.xml --lang ru-RU --maxitems 50 --user zaraz7
```
### Blog
It can generate blog feed from .txt files of `/blog` directory. If you want publications without description (content of your .txt files), only link to your web site and title, you can use `--no-description` flag.

[Example](https://zaraz7.narod.ws/blog.xml):
```bash
python3 w1f.py gen --type blog --url https://zaraz7.narod.ws --host ftp.narod.ws --title 'Блог Zaraz7' -o blog.xml --lang ru-RU -u zaraz7
```

[![Valid RSS v](https://www.rssboard.org/rss-validator/images/valid-rss-rogers.png)](https://www.rssboard.org/rss-validator/check.cgi?url=https%3A%2F%2Fzaraz7.narod.ws%2Fimg.xml)

## TODO
- [ ] Additional generators
  - [x] For /blog
  - [ ] Simple log parse
  - [ ] Neocities like feed
- [x] Config for similar generations
- [ ] Setup?
- [ ] Service unit or cron script
- [ ] localhost option
