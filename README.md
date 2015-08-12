## DTU Resume Manager Scrapper

It scraps all the updates from the Resume Manager of Delhi Technological
University and sends an E-mail Notification about the latest Announcements.


## Dependencies

If you’re on Debian or Ubuntu Linux, you can install Beautiful Soup and mechanize with the system package manager:

* BeautifulSoup
```
$ apt-get install python-bs4
```

* Mechanize

```
apt-get install python-mechanize
```

## Automation

This script is hosted on Google App Engine, with cron job (every 15 minutes). 

# Instructions

1. Add your credentials in the Globals/Email section in `dturmscrap.py`.

 * `'YOUR_ROLL_NUMBER,` e.g: `2K12/BR/001'`
 * `'PASSWORD'`
 * `sender_address = 'admin@dturm-1021.appspotmail.com'  # : for e.g. 'foo@appname.appspotmail.com'`
 * `'YOUR_EMAIL_ADDRESS'`

2. Deploy on [Google AppEngine](http://appengine.google.com)

## Contributing

All contributions are welcome, feel free to report an issue or send in a PR.
