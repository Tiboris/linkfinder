#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
# import threading
import errno

from copy import deepcopy
from urllib.request import urlopen
from bs4 import BeautifulSoup
from xml.etree import ElementTree as et
from post import Post
import signal


def signal_handler(sig, frame):
    print('\nTerminated with SIGINT')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


# class myThread (threading.Thread):
#     s = 0
#     e = 0

#     def __init__(self, start, end, name):
#         threading.Thread.__init__(self)
#         self.name = name
#         self.s = start
#         self.e = end
#         self.name = name

#     def run(self):
#         print("Starting", self.name)
#         init_mode(self.name, self.s, self.e)
#         print("Exiting", self.name)


def parse_posts(html):
    soup = BeautifulSoup(html, "lxml")

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
    for x in range(0, len(rows2)):
        rows.insert(cnt, rows2[x])
        cnt += 2

    if len(rows) is not len(names) or len(names) is not len(post_details):
        sys.stderr.write("Error\n")
        exit(1)

    posted = []
    subjects = []

    for x in post_details:
        text = str(x.text)
        posted.append(text[0][8:])
        subjects.append(text[1][14:])

    posts = []

    for x in range(0, len(names)):
        post = Post(
            str(names[x].text),
            posted[x], subjects[x],
            str(rows[x].text)
        )
        posts.append(post)

    return posts


forum_link = "https://forums.gentoo.org/"
root = et.Element('root')


def get_topics_from_forum(forum, name):
    page = 0
    pagesize = 50
    topics = set()

    while True:
        composed_url = forum_link + forum + \
            "-topicdays-0-start-" + str(page) + ".html"

        response = urlopen(composed_url)

        try:
            html = response.read()
        except Exception:
            break

        if page == 0 and "The topic or post you requested " \
                "does not exist" in str(html, "utf-8"):
            break

        if "No posts exist for this topic" in str(html, "utf-8"):
            break
        if "There are no posts in this forum." in str(html, "utf-8"):
            break
        if "Please enter your username and " \
                " password to log in." in str(html, "utf-8"):
            break

        soup = BeautifulSoup(html, "lxml")

        topics_table_tags = soup.find("table", {
            "width": "100%", "cellpadding": "4", "cellspacing": "1",
            "class": "forumline", "border": "0",
            }
        )

        guidelines = 0
        for item in topics_table_tags:
            soup = BeautifulSoup(str(item), "lxml")
            if soup.find_all("b"):
                guidelines += 1

        counter = 0
        for row in topics_table_tags:
            soup = BeautifulSoup(str(row), "lxml")

            topicid = soup.find("a", {
                "class": "topictitle"
            })

            if topicid:
                counter += 1
                topics.add(topicid["href"].split(".")[0])

        if counter == guidelines:
            break  # same topics on onexiting pages - Announcements

        new_message = "Forum [{}] - topics to download: {}\r".format(
            name, len(topics)
        )

        sys.stdout.flush()
        sys.stdout.write(new_message)

        page += pagesize

    return topics


def get_all_forums_topics(endpoint="index.php"):

    all_forums = []

    response = urlopen(forum_link + endpoint)

    try:
        html = response.read()
    except Exception:
        sys.stderr.write("An error happened!")
        exit(1)

    if "Please enter your username and " \
            " password to log in." in str(html, "utf-8"):
        sys.stderr.write("An error happened!")
        exit(1)

    soup = BeautifulSoup(html, "lxml")

    forums_table = soup.findAll("table", {
        "width": "100%", "cellpadding": "2", "cellspacing": "1",
        "class": "forumline", "border": "0"
        }
    )[1]

    for row in forums_table:
        soup = BeautifulSoup(str(row), "lxml")
        forumid = soup.find("a", {
            "class": "forumlink"
        })
        if forumid:
            all_forums.append(
                (forumid["href"].split(".")[0], forumid.contents[0])
            )

    topics = set()
    HREF = 0
    NAME = 1
    sys.stdout.write("Forum cnt: {}\n".format(len(all_forums)))

    for forum in all_forums:
        topics.update(get_topics_from_forum(forum[HREF], forum[NAME]))
        sys.stdout.write("\n")

    return topics


def init_mode(thread_name, topic_id):
    return True

# threads = []

# for i in range(0, 15):
#     threads.append(myThread(count/16*i, count/16*(i+1), str(i+1)))

# for t in threads:
#     t.start()

# for t in threads:
#     t.join()


def single_run():
    topic_counter = 0

    thread_name = "Main"
    newroot = deepcopy(root)

    all_topics = get_all_forums_topics()

    sys.stdout.write("Topic cnt TOTAL: {}\n".format(len(all_topics)))
    exit(0)  # stop here not to donwnload yet

    for topic_id in all_topics:
        posts = []
        page = 0

        while 1:
            response = urlopen(
                forum_link + str(topic_id) +
                "-postdays-0-postorder-asc-start-" + str(page) + ".html"
            )

            try:
                html = response.read()
            except Exception:
                break

            if page == 0 and "The topic or post you requested " \
                    "does not exist" in str(html, "utf-8"):
                break

            if "No posts exist for this topic" in str(html, "utf-8"):
                break
            if "Please enter your username and " \
                    " password to log in." in str(html, "utf-8"):
                break

            name = forum_link + str(topic_id) + \
                "-postdays-0-postorder-asc-start-" + str(page)

            print(thread_name + "\t: " + topic_id + ".html")

            soup = BeautifulSoup(html, "lxml")

            posts += parse_posts(html)

            if page == 0:
                topic_counter += 1

            page += 25

        if soup:
            topic = et.Element("topic")
            topic_index = et.Element("topic_index")
            topic_index.text = str(topic_id)
            topic.append(topic_index)
            topic_name = et.Element("topic_name")
            text = soup.title.string.encode('unicode-escape')
            topic_name.text = text.decode('unicode-escape')
            topic.append(topic_name)
            topic_address = et.Element("topic_address")
            topic_address.text = forum_link + "viewtopic-t-" + str(topic_index) \
                + "-postdays-0-postorder-asc-start-" + str(page) + ".html"
            topic.append(topic_address)

            for x in posts:
                topic_post = et.Element("topic_post")

                post_page_offset = et.Element("post_page_offset")
                post_page_offset.text = str(page-25)

                post_author = et.Element("post_author")
                post_author.text = x.author

                post_posted = et.Element("post_posted")
                post_posted.text = x.posted

                post_subject = et.Element("post_subject")
                post_subject.text = x.subject

                post_text = et.Element("post_text")
                post_text.text = x.text

                topic_post.append(post_page_offset)
                topic_post.append(post_author)
                topic_post.append(post_posted)
                topic_post.append(post_subject)
                topic_post.append(post_text)

                topic.append(topic_post)

            newroot.append(topic)

            dest = "./download"

            print(len(posts))

            try:
                os.mkdir(dest)
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
                pass

            with open("{}/{}.xml".format(dest, topic_id + ".html"), "wb") as f:
                xmlstr = et.tostring(newroot, encoding='utf8', method='xml')
                f.write(xmlstr)
                print("Saving:", name + ".html")


single_run()
