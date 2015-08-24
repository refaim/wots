# coding: utf-8

import codecs
import functools
import itertools
import json
import multiprocessing
import os
import Queue
import sys
import threading
import webbrowser
import wx
import wx.grid

import card.sets
import card.sources
import card.utils
import core.currency
import core.logger
import price.sources
import ui.autocomplete
import ui.smartgrid


_LETTERS = core.language.LOWERCASE_LETTERS_ENGLISH | core.language.LOWERCASE_LETTERS_RUSSIAN


def getCardCompletionKey(cardname):
    return u''.join(c for c in card.utils.escape(cardname).lower() if c in _LETTERS)


def getResourcePath(resourceId):
    return os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'resources', resourceId))


class MainWindow(wx.Frame):
    def __init__(self):
        with codecs.open(getResourcePath('autocomplete.json'), 'r', 'utf-8') as data:
            self.cardCompletions = json.load(data)

        self.currencyConverter = core.currency.Converter()
        self.currencyConverter.update()

    def autoCompleteCard(self, query):
        cards = {}
        completionKey = getCardCompletionKey(query)
        if len(completionKey) >= 2:
            for key, values in self.cardCompletions.iteritems():
                for value in values:
                    if completionKey in key and value not in cards:
                        cards[value] = key
        result = sorted(cards.iterkeys(), cmp=functools.partial(self.sortCardCompletions, completionKey, cards))
        if query in result and sum(int(card.startswith(query.strip())) for card in result) == 1:
            result = []
        return (result, result)

    def sortCardCompletions(self, completionKey, cardsByValue, a, b):
        av, bv = cardsByValue[a], cardsByValue[b]
        if av.startswith(completionKey):
            return -1
        if bv.startswith(completionKey):
            return 1
        return -1 if a <= b else 1

    def OnClose(self, event):
        self.searchStopEvent.set()
        self.priceRetrieverStopEvent.set()
        event.Skip()

    def OnCardFound(self, event):
        self.foundCards.put((event.cardInfo, event.cookie))

    def OnPriceObtained(self, event):
        self.obtainedPrices.put((event.jobId, event.priceInfo, event.cookie))

    def OnInterfaceUpdateTimerTick(self, event):
        newCards = []
        newRows = []
        changedCells = []
        while not self.foundCards.empty():
            cardInfo, cookie = self.foundCards.get(block=False)
            if cookie == self.searchVersion and cardInfo['count'] > 0:
                if cardInfo.get('price'):
                    cardInfo['price'] = self.packPrice(cardInfo['price'], cardInfo['currency'])
                row = []
                columnCount = self.resultsGrid.GetNumberCols()
                for columnIndex in xrange(columnCount):
                    row.append(cardInfo.get(SEARCH_RESULTS_TABLE_COLUMNS_INFO[columnIndex]['id'], ''))
                newCards.append(cardInfo)
                newRows.append(row)

        while not self.obtainedPrices.empty():
            rowId, priceInfo, cookie = self.obtainedPrices.get(block=False)
            if cookie == self.searchVersion and priceInfo:
                columnIndex = -1
                for i, columnInfo in enumerate(SEARCH_RESULTS_TABLE_COLUMNS_INFO):
                    if columnInfo['id'] == priceInfo['source_id']:
                        columnIndex = i
                changedCells.append((rowId, columnIndex, self.packPrice(priceInfo['price'], priceInfo['currency'])))

        if newRows or changedCells:
            newRowsIds = self.resultsGrid.Populate(newRows, changedCells)
            for rowId, cardInfo in itertools.izip(newRowsIds, newCards):
                if cardInfo.get('set'):
                    self.priceRequests.put((rowId, self.searchVersion, cardInfo['name']['caption'], cardInfo['set'], cardInfo['language'], cardInfo.get('foilness', False),))
            if newRows:
                self.statusBar.SetStatusText('{} cards found. Searching...'.format(self.resultsGrid.GetNumberRows()))
