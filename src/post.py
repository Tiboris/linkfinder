# -*- coding: utf-8 -*-


class Post():

    author = ""
    posted = ""
    subject = ""
    text = ""

    def __init__(self, author, posted, subject, text):

        self.author = author
        self.author = self.author.decode('utf-8').encode('unicode-escape')
        self.author = self.author.decode('unicode-escape')

        self.posted = posted
        self.posted = self.posted.decode('utf-8').encode('unicode-escape')
        self.posted = self.posted.decode('unicode-escape')

        self.subject = subject
        self.subject = self.subject.decode('utf-8').encode('unicode-escape')
        self.subject = self.subject.decode('unicode-escape')

        self.text = text.replace('\n', '\\n')
        self.text = self.text.decode('utf-8').encode('unicode-escape')
        self.text = self.text.decode('unicode-escape')

    def __str__(self):
        string = "Author = " + self.author + " : " + \
            "Posted = " + self.posted + " : " + \
            "Subject = " + self.subject + " : " + \
            "Text = " + self.text

        return string
