#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from post import Post
from bs4 import BeautifulSoup
from urllib.request import urlopen


forum_link = "https://forums.gentoo.org/"


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


def get_all_forums_topics(endpoint="index.php", get_all=True):

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

    if not get_all:  # run only on sample forums
        all_forums = [all_forums[1], all_forums[0]]

    topics = set()
    HREF = 0
    NAME = 1
    sys.stdout.write("Forum cnt: {}\n".format(len(all_forums)))


    for forum in all_forums:
        topics.update(get_topics_from_forum(forum[HREF], forum[NAME]))
        sys.stdout.write("\n")

    return topics
