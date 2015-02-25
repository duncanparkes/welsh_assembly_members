# This is a morph.io scraper

import scraperwiki
import lxml.html
import re


seating_plan_html = scraperwiki.scrape('http://www.assembly.wales/en/memhome/Pages/mem-seating-plan.aspx')
sp_root = lxml.html.fromstring(seating_plan_html)
links = sp_root.cssselect('table a')
print '{} links found'.format(len(links))

name_re = re.compile(r'([\w\s]*\w)\s*(?:\(([\w\s]*)\))?')
names = set()

for a in sp_root.cssselect('table a'):
  am = {}
  am_link = a.get('href')
  # print am_link
  am['href'] = am_link
  am['id'] = am_link.rsplit('=', 1)[-1]

  am_html = scraperwiki.scrape(am_link)
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
  if 'en_title' in am:
    am['post'] = 'Commissioner-{}'.format(group) if title == 'Commissioner' else title

  scraperwiki.sqlite.save(unique_keys=['name'], data=am)


# # An arbitrary query against the database
# scraperwiki.sql.select("* from data where 'name'='peter'")

# You don't have to do things with the ScraperWiki and lxml libraries. You can use whatever libraries are installed
# on Morph for Python (https://github.com/openaustralia/morph-docker-python/blob/master/pip_requirements.txt) and all that matters
# is that your final data is written to an Sqlite database called data.sqlite in the current working directory which
# has at least a table called data.
