# -*- coding: utf-8 -*-
__license__ = """Copyright (c) 2008-2010, Toni Ruža, All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 'AS IS'
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE."""

__author__ = u"Toni Ruža <gmr.gaf@gmail.com>"
__url__  = "http://bitbucket.org/raz/wxautocompletectrl"


import sys
import os
import random
import string
import wx
from autocomplete import AutocompleteTextCtrl


template = "%s<b><u>%s</b></u>%s"


def random_list_generator(query):
    formatted, unformatted = list(), list()
    if query:
        for i in xrange(random.randint(0, 30)):
            prefix = "".join(random.sample(string.letters, random.randint(0, 10)))
            postfix = "".join(random.sample(string.letters, random.randint(0, 10)))
            value = (prefix, query, postfix)
            formatted.append(template % value)
            unformatted.append("".join(value))

    return formatted, unformatted


def list_completer(a_list):
    def completer(query):
        formatted, unformatted = list(), list()
        if query:
            unformatted = [item for item in a_list if query in item]
            for item in unformatted:
                s = item.find(query)
                formatted.append(
                    template % (item[:s], query, item[s + len(query):])
                )

        return formatted, unformatted
    return completer


def test():
    some_files = [
        name
        for path in sys.path if os.path.isdir(path)
        for name in os.listdir(path)
    ]
    quotes = open("taglines.txt").read().split("%%")

    app = wx.App(False)
    app.TopWindow = frame = wx.Frame(None)
    frame.Sizer = wx.FlexGridSizer(3, 2, 5, 5)
    frame.Sizer.AddGrowableCol(1)
    frame.Sizer.AddGrowableRow(2)

    # A completer must return two lists of the same length based
    # on the "query" (current value in the TextCtrl).
    #
    # The first list contains items to be shown in the popup window
    # to the user. These items can use HTML formatting. The second list
    # contains items that will be put in to the TextCtrl, usually the
    # items from the first list striped of formating.

    field1 = AutocompleteTextCtrl(frame, completer=random_list_generator)
    field2 = AutocompleteTextCtrl(frame, completer=list_completer(some_files))
    field3 = AutocompleteTextCtrl(
        frame, completer=list_completer(quotes), multiline=True
    )

    frame.Sizer.Add(wx.StaticText(frame, label="Random strings"))
    frame.Sizer.Add(field1, 0, wx.EXPAND)
    frame.Sizer.Add(wx.StaticText(frame, label="Files in sys.path"))
    frame.Sizer.Add(field2, 0, wx.EXPAND)
    frame.Sizer.Add(wx.StaticText(frame, label="Famous quotes"))
    frame.Sizer.Add(field3, 0, wx.EXPAND)
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    test()
