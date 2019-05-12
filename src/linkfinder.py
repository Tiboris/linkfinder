import os
import sys
import time
import errno
import numpy
import signal
import argparse
import gentoo_fetcher

from bs4 import BeautifulSoup
from urllib.request import urlopen
from xml.etree import ElementTree as et


def signal_handler(sig, frame):
    print('\nTerminated with SIGINT')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
forum_link = "https://forums.gentoo.org/"
dest = "./download"

T = "threads"
S = "sample"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default="1",
        required=False,
        help="Number of threads to use",
    )
    parser.add_argument(
        "-s",
        "--sample",
        default=False,
        action="store_true",
        required=False,
        help="Show realtime rendering.",
    )

    return parser.parse_args()


def process_topics(topics, thread=1):
    topic_counter = 0
    for topic_id in topics:
        thread_name = "T_" + str(thread)
        posts = []
        page = 0

        while 1:
            newroot = et.Element('root')
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

            full_link = forum_link + str(topic_id) + ".html"

            sys.stdout.flush()
            sys.stdout.write(thread_name + "\t: " + full_link + "\t| ")

            soup = BeautifulSoup(html, "lxml")

            posts += gentoo_fetcher.parse_posts(html)

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
            topic_address.text = forum_link + str(topic_index) \
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

        print("Number of posts:", len(posts))

        with open("{}/{}.xml".format(dest, topic_id + ".html"), "wb") as f:
            xmlstr = et.tostring(newroot, encoding='utf8', method='xml')
            f.write(xmlstr)


def run(threads, sample):
    start_time = time.time()

    try:
        os.mkdir(dest)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass

    all_topics = gentoo_fetcher.get_all_forums_topics(get_all=sample)
    sys.stdout.write("Topics TOTAL: {}\n".format(len(all_topics)))

    pids = []
    if threads == 1:
        process_topics(all_topics, threads)
    else:
        all_topics = numpy.array_split(list(all_topics), threads)

        for thread in range(threads):
            pid = os.fork()
            pids.append(pid)

            if pid == 0:
                process_topics(all_topics[thread], os.getpid())
                exit(0)
            else:
                continue

    for pid in pids:
        os.waitpid(pid, 0)

    print("Total time:", time.time() - start_time)

    exit(0)


if __name__ == "__main__":
    args = vars(parse_args())
    run(args[T], args[S])
