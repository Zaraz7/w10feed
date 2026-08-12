# w10feed
<!-- TODO: надо бы добавить описание на русском -->
Generator RSS 2.0 feed for [HamsterCMS](http://hamster.oldcities.org) sites and [Web1.0 Hosting](http://w10.host) sites

## Feachers
### Ocular Webring like feed
I did this primarily for myself, because I wanted to join the party of [subversive.pics](https://img.triapul.cz/sect.html) or [Ocular Webring](https://codeberg.org/rostiger/ocular_webring).
It It generates a news feed with pictures based on your site's `/photos` directory.

[Example](https://zaraz7.narod.ws/img.xml):

```bash
w10feed.py gen --type pics --url "https://zaraz7.narod.ws" --user zaraz7 --host ftp.narod.ws --title "Zaraz7's Gallery" -o img.xml --lang ru-RU -p password_example
```



## TODO
- Additional generators
  - For /blog
  - Neocities like feed
- Config for similar generations