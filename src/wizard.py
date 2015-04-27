# coding: utf-8

import codecs
import functools
import json
import multiprocessing
import os
import Queue
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

WINDOW_TITLE = 'Wizard of the Search'

EVT_CARD_FOUND = wx.NewId()
EVT_SEARCH_COMPLETE = wx.NewId()
EVT_PRICE_OBTAINED = wx.NewId()


def escapeNone(value):
    return value if value is not None else ''


SEARCH_RESULTS_TABLE_ROW_COUNT = 30
SEARCH_RESULTS_TABLE_COLUMNS_INFO = [
    {
        'id': 'id',
        'label': '#',
        'horz_alignment': wx.ALIGN_RIGHT,
        'formatter': lambda x: str(x).zfill(3) if x else ''
    },
    {
        'id': 'set',
        'label': 'Set',
        'horz_alignment': wx.ALIGN_CENTER,
        'formatter': escapeNone,
        'tooltipper': lambda x: card.sets.getFullName(x) if x else '',
    },
    {
        'id': 'language',
        'label': 'LNG',
        'horz_alignment': wx.ALIGN_CENTER,
        'formatter': escapeNone
    },
    {
        'id': 'name',
        'label': 'Name',
        'horz_alignment': wx.ALIGN_LEFT,
        'formatter': lambda x: card.utils.unescape(x['caption']),
        'sort_key': lambda x: x['caption'],
        'tooltipper': lambda x: x.get('description')
    },
    {
        'id': 'condition',
        'label': 'CND',
        'horz_alignment': wx.ALIGN_CENTER,
        'formatter': escapeNone
    },
    {
        'id': 'foilness',
        'label': 'Foil',
        'horz_alignment': wx.ALIGN_CENTER,
        'formatter': lambda x: 'Foil' if x else ''
    },
    {
        'id': 'count',
        'label': 'Count',
        'horz_alignment': wx.ALIGN_RIGHT
    },
    {
        'id': 'price',
        'label': 'Price',
        'horz_alignment': wx.ALIGN_RIGHT,
        'formatter': lambda x: u'{}₽'.format(int(x)) if x else ''
    },
    {
        'id': 'source',
        'label': 'Source',
        'horz_alignment': wx.ALIGN_LEFT,
        'formatter': lambda x: x['caption'],
        'sort_key': lambda x: x['caption'],
        'on_click': lambda x: webbrowser.open_new_tab(x['url']),
    },
]

_LETTERS = core.language.LOWERCASE_LETTERS_ENGLISH | core.language.LOWERCASE_LETTERS_RUSSIAN


def getCardCompletionKey(cardname):
    return u''.join(c for c in card.utils.escape(cardname).lower() if c in _LETTERS)


class CardFoundEvent(wx.PyEvent):
    def __init__(self, cardInfo):
        super(CardFoundEvent, self).__init__()
        self.SetEventType(EVT_CARD_FOUND)
        self.cardInfo = cardInfo


class SearchCompleteEvent(wx.PyEvent):
    def __init__(self):
        super(SearchCompleteEvent, self).__init__()
        self.SetEventType(EVT_SEARCH_COMPLETE)


class PriceObtainedEvent(wx.PyEvent):
    def __init__(self, priceInfo):
        super(PriceObtainedEvent, self).__init__()
        self.SetEventType(EVT_PRICE_OBTAINED)
        self.priceInfo = priceInfo


def getResourcePath(resourceId):
    return os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'resources', resourceId))


class MainWindow(wx.Frame):
    def __init__(self):
        super(MainWindow, self).__init__(
            parent=None,
            title=WINDOW_TITLE,
            style=wx.DEFAULT_FRAME_STYLE)

        self.SetIcon(wx.Icon(getResourcePath('magnifier.png'), wx.BITMAP_TYPE_PNG))

        with codecs.open(getResourcePath('autocomplete.json'), 'r', 'utf-8') as data:
            self.cardCompletions = json.load(data)

        self.searchInProgress = False
        self.searchStopEvent = threading.Event()
        self.priceRequests = Queue.Queue()
        self.priceRetrieverStopEvent = threading.Event()
        self.priceRetriever = threading.Thread(name='Prices', target=priceRetriever, args=(self.priceRequests, self, self.priceRetrieverStopEvent,))
        self.priceRetriever.daemon = True
        self.priceRetriever.start()

        self.currencyConverter = core.currency.Converter()
        self.currencyConverter.update()

        self.Connect(id=-1, lastId=-1, eventType=EVT_CARD_FOUND, func=self.OnCardFound)
        self.Connect(id=-1, lastId=-1, eventType=EVT_SEARCH_COMPLETE, func=self.OnSearchComplete)
        self.Connect(id=-1, lastId=-1, eventType=EVT_PRICE_OBTAINED, func=self.OnPriceObtained)

        # menuFile = wx.Menu()
        # self.Bind(wx.EVT_MENU, self.OnExit, menuFile.Append(wx.ID_EXIT, 'E&xit'))

        # mainMenu = wx.MenuBar()
        # mainMenu.Append(menuFile, '&File')
        # self.SetMenuBar(mainMenu)

        self.statusBar = self.CreateStatusBar()

        self.interfacePanel = wx.Panel(parent=self)
        self.interfacePanelSizer = wx.BoxSizer(orient=wx.VERTICAL)
        self.interfacePanel.SetSizer(self.interfacePanelSizer)

        self.controlPanel = wx.Panel(parent=self.interfacePanel)
        self.controlPanelSizer = wx.BoxSizer(orient=wx.VERTICAL)
        self.controlPanel.SetSizer(self.controlPanelSizer)

        self.searchPanel = wx.Panel(parent=self.controlPanel, size=wx.Size(500, -1))
        self.searchPanelSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        self.searchPanel.SetSizer(self.searchPanelSizer)

        self.searchField = ui.autocomplete.AutocompleteTextCtrl(parent=self.searchPanel, height=150, completer=self.autoCompleteCard)
        self.searchField.Bind(wx.EVT_KEY_DOWN, self.OnSearchFieldKeyDown)
        self.searchField.Bind(wx.EVT_KEY_UP, self.OnSearchFieldKeyUp)
        self.searchButton = wx.Button(parent=self.searchPanel, label='Search')
        self.searchButton.Bind(wx.EVT_BUTTON, self.OnSearchButtonClick)
        self.searchButton.Disable()

        self.searchPanelSizer.Add(item=self.searchField, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        self.searchPanelSizer.Add(item=self.searchButton, flag=wx.ALIGN_CENTER_VERTICAL)

        # self.filterPanel = wx.Panel(parent=self.controlPanel)
        # self.filterPanelSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        # self.filterPanel.SetSizer(self.filterPanelSizer)

        # self.filterLabel = wx.StaticText(parent=self.filterPanel, label='Filter')
        # self.filterField = wx.TextCtrl(parent=self.filterPanel)
        # self.filterPanelSizer.Add(item=self.filterLabel, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        # self.filterPanelSizer.Add(item=self.filterField, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL)

        self.controlPanelSizer.Add(item=self.searchPanel, flag=wx.ALL, border=5)
        # self.controlPanelSizer.Add(item=self.filterPanel, flag=wx.EXPAND | wx.ALL, border=5)

        self.resultsGrid = ui.smartgrid.SmartGrid(parent=self.interfacePanel)
        self.resultsGrid.EnableEditing(edit=False)
        self.resultsGrid.EnableDragRowSize(enable=False)
        self.resultsGrid.EnableDragColSize(enable=False)
        self.resultsGrid.SetDefaultCellFont(wx.Font(pointSize=11, family=wx.FONTFAMILY_MODERN, style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_NORMAL, underline=False, face='Consolas'))
        self.resultsGrid.CreateGrid(numRows=SEARCH_RESULTS_TABLE_ROW_COUNT, columnsSetup=SEARCH_RESULTS_TABLE_COLUMNS_INFO, selMode=wx.grid.Grid.SelectRows)
        self.resultsGridSizer = wx.BoxSizer()
        self.resultsGridSizer.Add(item=self.resultsGrid, proportion=1, flag=wx.ALL | wx.EXPAND)

        self.interfacePanelSizer.Add(item=self.controlPanel, flag=wx.EXPAND | wx.ALL, border=5)
        self.interfacePanelSizer.Add(item=self.resultsGrid, proportion=2, flag=wx.EXPAND)

        self.windowSizer = wx.BoxSizer(orient=wx.VERTICAL)
        self.windowSizer.Add(item=self.interfacePanel, flag=wx.EXPAND | wx.ALL)

        self.SetSizer(self.windowSizer)
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.Centre()

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

    def OnExit(self, event):
        self.Close()

    def OnCardFound(self, event):
        cardInfo = event.cardInfo
        if cardInfo['count'] <= 0:
            return

        cardPrice = cardInfo.get('price', None)
        priceCurrency = cardInfo.get('currency', None)
        if priceCurrency is not None and cardPrice is not None and priceCurrency != core.currency.RUR:
            cardInfo['price'] = self.currencyConverter.convert(priceCurrency, core.currency.RUR, cardPrice)

        rowData = []
        columnCount = self.resultsGrid.GetNumberCols()
        for columnIndex in xrange(columnCount):
            columnSetup = SEARCH_RESULTS_TABLE_COLUMNS_INFO[columnIndex]
            value = cardInfo.get(columnSetup['id'].lower(), '')
            rowData.append(value)
        rowIndex = self.resultsGrid.AddRow(rowData)
        for columnIndex in xrange(columnCount):
            self.resultsGrid.AutoSizeColumn(columnIndex)
        self.resultsGrid.AutoSizeRow(rowIndex)
        self.statusBar.SetStatusText('{} cards found. Searching...'.format(self.resultsGrid.GetNumberRows()))
        # if 'set' in cardInfo and 'language' in cardInfo and cardInfo['language'] is not None:
        #     self.priceRequests.put((cardInfo['name'], cardInfo['set'], cardInfo['language'], cardInfo.get('foilness', False),))

    def OnSearchComplete(self, event):
        self.searchInProgress = False
        self.searchField.Enable()
        self.searchButton.Enable()
        self.searchButton.SetLabel('Search')
        self.statusBar.SetStatusText('{} cards found.'.format(self.resultsGrid.GetNumberRows()))

    def OnSearchFieldKeyDown(self, event):
        keyCode = event.GetKeyCode()
        if keyCode in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER] and not self.searchField.popup.Shown and not self.searchInProgress:
            self.searchCards()
        event.Skip()

    def OnSearchFieldKeyUp(self, event):
        self.searchButton.Enable(len(self.searchField.GetValue()) > 0)
        event.Skip()

    def OnSearchButtonClick(self, event):
        if self.searchInProgress:
            self.searchStopEvent.set()
            self.searchButton.Disable()
        else:
            self.searchCards()

    def searchCards(self):
        queryString = self.searchField.GetValue().strip()
        if not queryString:
            return
        queryString = card.utils.escape(queryString)

        self.searchInProgress = True
        self.searchField.Disable()
        self.searchButton.SetLabel('Stop')
        self.statusBar.SetStatusText('Searching...')
        rowCount = self.resultsGrid.GetNumberRows()
        if rowCount > 0:
            self.resultsGrid.ClearGrid()
            self.resultsGrid.DeleteRows(pos=0, numRows=rowCount)

        self.searchStopEvent.clear()
        self.searchThread = threading.Thread(name='Search', target=searchCards, args=(queryString, self, self.searchStopEvent))
        self.searchThread.daemon = True
        self.searchThread.start()

    def OnPriceObtained(self, event):
        # print(event.priceInfo)
        pass


def queryCardSource(cardSource, queryString, results, exitEvent):
    for cardInfo in cardSource.query(queryString):
        if exitEvent.is_set():
            return
        results.put(cardInfo)


def searchCards(queryString, wxEventBus, exitEvent):
    results = multiprocessing.Queue()
    terminators = []
    workers = []
    for sourceClass in card.sources.getCardSourceClasses():
        source = sourceClass()
        event = multiprocessing.Event()
        terminators.append(event)
        workers.append(multiprocessing.Process(name=source.getTitle(), target=queryCardSource, args=(source, queryString, results, event,)))
    for process in workers:
        process.daemon = True
        process.start()

    while any(process.is_alive() for process in workers) or not results.empty():
        try:
            wx.PostEvent(wxEventBus, CardFoundEvent(results.get(block=False)))
        except Queue.Empty:
            pass
        if exitEvent.is_set():
            for terminator in terminators:
                terminator.set()
            break

    for process in workers:
        process.join()

    wx.PostEvent(wxEventBus, SearchCompleteEvent())


def processPriceRequests(processor, requests, results):
    while True:
        cardName, setId, language, foilness = requests.get()
        results.put(processor.queryPrice(cardName, setId, language, foilness))


def priceRetriever(taskQueue, wxEventBus, exitEvent):
    requests = multiprocessing.Queue()
    results = multiprocessing.Queue()
    workers = []
    for source in price.sources.getPriceSourceClasses():
        source = source()
        workers.append(multiprocessing.Process(name=source.getTitle(), target=processPriceRequests, args=(source, requests, results,)))
    for process in workers:
        process.daemon = True
        process.start()
    while not exitEvent.is_set():
        try:
            while not taskQueue.empty():
                requests.put(taskQueue.get(block=False))
            while not results.empty():
                wx.PostEvent(wxEventBus, PriceObtainedEvent(results.get(block=False)))
        except Queue.Empty:
            pass


if __name__ == '__main__':
    application = wx.App(redirect=False)
    window = MainWindow()
    window.Show()
    application.MainLoop()
