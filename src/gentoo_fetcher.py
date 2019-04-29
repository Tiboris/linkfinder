#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
from bs4 import BeautifulSoup
import sys
from post import Post
from lxml import etree
import threading


class myThread (threading.Thread):
    s = 0
    e = 0

    def __init__(self, start, end, name):
        threading.Thread.__init__(self)
        self.name = name
        self.s = start
        self.e = end
        self.name = name

    def run(self):
        print "Starting " + self.name
        init_mode(self.name, self.s, self.e)
        print "Exiting " + self.name


def get_num_of_topics():
    response = urllib2.urlopen("https://forums.gentoo.org/statistics.php")
    html = response.read()

    soup = BeautifulSoup(html)

    table = soup.find("table", {
        "border": "0", "cellpadding": "4", "cellspacing": "1",
        "class": "forumline", "width": "100%"
        }
    )

    string = None
    for x in table:
        if "Number of topics" in str(x):
            spans = x.find_all("span", {"class": "gen"})
            return int(spans[1].text)


def parse_posts(html):
    soup = BeautifulSoup(html)

    rows1 = soup.find_all("td", {
        "class": "row1", "width": "100%", "height": "28", "valign": "top"
        }
    )
    rows2 = soup.find_all("td", {
        "class": "row2", "width": "100%", "height": "28", "valign": "top"
        }
    )
    names = soup.find_all("span", {"class": "name"})
    post_details = soup.find_all("span", {"class": "postdetails"})[1::2]

    rows = rows1

    cnt = 1
    for x in xrange(0, len(rows2)):
        rows.insert(cnt, rows2[x])
        cnt += 2

    if len(rows) is not len(names) or len(names) is not len(post_details):
        sys.stderr.write("Error\n")
        exit(1)

    posted = []
    subjects = []

    for x in post_details:
        text = unicode(x.text).encode("utf-8").split("\xc2\xa0\xc2\xa0 \xc2\xa0")
        posted.append(text[0][8:])
        subjects.append(text[1][14:])

    posts = []

    for x in xrange(0, len(names)):
        post = Post(names[x].text.encode("utf-8"), posted[x], subjects[x], rows[x].text.encode("utf-8"))
        posts.append(post)

    return posts


forum_link = "https://forums.gentoo.org/"
root = etree.Element('root')


def init_mode(thread_name, start, end):

    index = start
    topic_counter = 0

    while 1:
        page = 0
        posts = []
        soup = None
        while 1:
            response = urllib2.urlopen(
                forum_link + "viewtopic-t-"
                + str(index) + "-postdays-0-postorder-asc-start-"
                + str(page) + ".html")

            html = response.read()

            if page == 0 and \
                    "The topic or post you requested does not exist" in html:
                break
            if "No posts exist for this topic" in html:
                break
            if "Please enter your username and password to log in." in html:
                break

            print thread_name + " : " + forum_link + "viewtopic-t-" \
                + str(index) + "-postdays-0-postorder-asc-start-" \
                + str(page) + ".html"

            soup = BeautifulSoup(html)
            posts += parse_posts(html)

            if page == 0:
                topic_counter += 1
            page += 25

        if soup:
            topic = etree.Element("topic")
            topic_index = etree.Element("topic_index")
            topic_index.text = str(index)
            topic.append(topic_index)
            topic_name = etree.Element("topic_name")
            text = soup.title.string.encode('unicode-escape')
            topic_name.text = text.decode('unicode-escape')
            topic.append(topic_name)
            topic_address = etree.Element("topic_address")
            topic_address.text = forum_link + "viewtopic-t-" + str(index) \
                + "-postdays-0-postorder-asc-start-" + str(page) + ".html"
            topic.append(topic_address)

            for x in posts:
                topic_post = etree.Element("topic_post")

                post_page_offset = etree.Element("post_page_offset")
                post_page_offset.text = str(page-25)

                post_author = etree.Element("post_author")
                post_author.text = x.author

                post_posted = etree.Element("post_posted")
                post_posted.text = x.posted

                post_subject = etree.Element("post_subject")
                post_subject.text = x.subject

                # print list(x.text)
                post_text = etree.Element("post_text")
                post_text.text = x.text

                topic_post.append(post_page_offset)
                topic_post.append(post_author)
                topic_post.append(post_posted)
                topic_post.append(post_subject)
                topic_post.append(post_text)

                topic.append(topic_post)

            root.append(topic)

        if index == end:
            break

        index += 1


threads = []

count = get_num_of_topics()

for i in xrange(0, 15):
    threads.append(myThread(count/16*i, count/16*(i+1), str(i+1)))

for t in threads:
    t.start()

for t in threads:
    t.join()


f = open("data.xml", "w")
f.write(etree.tostring(root, pretty_print=True))
f.close()
