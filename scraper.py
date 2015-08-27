# coding=utf-8

# This is a morph.io scraper

import scraperwiki
import lxml.html
import re
import urlparse


def scrape_url(url):
    html = scraperwiki.scrape(url)
    sp_root = lxml.html.fromstring(html)
    title = sp_root.cssselect('#ctl00_PlaceHolderMain_pageTitle')
    region_name = title[0].text.split(':')[-1].strip()
    links = sp_root.cssselect('.memberContainer h2 a')
    print '{} members found for {}'.format(len(links), region_name)
    for a in links:
        scrape_person(a.get('href'), region_name)


name_re = re.compile(r'([\w\s-]*\w)\s*(?:\(([\w\s]*)\))?')
names = set()


def scrape_person(url, region_name):
    am = {}
    am['href'] = url
    am['id'] = url.rsplit('=', 1)[-1]

    am_html = scraperwiki.scrape(url)
    am_root = lxml.html.fromstring(am_html)
    name = am_root.cssselect('h1')[0].text_content().strip()
    print 'Processing {}'.format(name)

    # We don't need the 'AM' suffix - they all have that.
    if name.endswith(' AM'):
        name = name[:-3]

    name, other_name = name_re.match(name).groups()
    am['name'] = name
    am['other_name'] = other_name

    if name in names:
        print "WARNING: duplicate name {}"
    names.add(name)

    sidebar_spans = am_root.cssselect('div.mgUserSideBar p span.mgLabel')
    for span in sidebar_spans:
        span_text = span.text.strip()
    span_tail = span.tail.strip()
    if span_text == 'Title:':
        title = am['en_title'] = span_tail
    elif span_text == 'Party:':
        group = am['group'] = am['en_party_name'] = span_tail
    elif span_text == 'Constituency:':
        am['en_constituency_name'] = span_tail
    elif span_text == 'Region:':
        am['en_region_name'] = span_tail

    am['area'] = am.get('en_constituency_name') or am.get('en_region_name')

    area_id = 'ocd-division/country:gb-wls/region:%s' % region_name
    constituency = am.get('en_constituency_name')
    if constituency:
        area_id = area_id + '/constituency:%s' % constituency
    am['area_id'] = area_id.replace(' ', '_').lower()

    if 'en_title' in am:
        if title == 'Commissioner':
            am['post'] = 'Commissioner-{}'.format(group)
        else:
            am['post'] = title

    am['image'] = urlparse.urljoin(
        url,
        am_root.cssselect('div.mgBigPhoto img')[0].attrib.get('src'),
        )

    msg_body_spans = am_root.cssselect('div.mgUserBody p span.mgLabel')
    for span in msg_body_spans:
        span_text = span.text.strip()
    span_tail = span.tail.strip()

    if 'Twitter' in span_text:
        am['twitter'] = span.getparent().find('a').get('href')
    elif 'Email' in span_text:
        am['email'] = span.getparent().find('a').get('href').replace('mailto:', '')

    scraperwiki.sqlite.save(unique_keys=['name'], data=am)


for n in range(1, 6):
    url_template = 'http://www.assembly.wales/en/memhome/Pages/membersearchresults.aspx?region={}'
    url = url_template.format(n)
    scrape_url(url)

# # An arbitrary query against the database
# scraperwiki.sql.select("* from data where 'name'='peter'")

# You don't have to do things with the ScraperWiki and lxml libraries. You can use whatever libraries are installed
# on Morph for Python (https://github.com/openaustralia/morph-docker-python/blob/master/pip_requirements.txt) and all that matters
# is that your final data is written to an Sqlite database called data.sqlite in the current working directory which
# has at least a table called data.
