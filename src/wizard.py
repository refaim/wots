import codecs
import io
import json
import math
import multiprocessing
import os
import platform
import psutil
import queue
import signal
import sys
import webbrowser

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic

import card.sources
import card.utils
import core.currency
import price.sources


def getResourcePath(resourceId):
    root = os.path.dirname(sys.executable)
    if not getattr(sys, 'frozen', False):
        root = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
    return os.path.normpath(os.path.join(root, 'resources', resourceId))


SEARCH_RESULTS_TABLE_COLUMNS_INFO = [
    {
        'id': 'number',
        'label': '#',
        'sources': ('id',),
        'align': QtCore.Qt.AlignRight,
        'default_value': 0,
    },
    {
        'id': 'set',
        'label': 'Set',
        'sources': ('set',),
        'align': QtCore.Qt.AlignHCenter,
        'default_value': '',
    },
    {
        'id': 'language',
        'label': 'LNG',
        'sources': ('language',),
        'align': QtCore.Qt.AlignHCenter,
        'default_value': '',
    },
    {
        'id': 'name',
        'label': 'Name',
        'sources': ('name',),
        'align': QtCore.Qt.AlignLeft,
        'default_value': '',
    },
    {
        'id': 'condition',
        'label': 'CND',
        'sources': ('condition',),
        'align': QtCore.Qt.AlignHCenter,
        'default_value': '',
    },
    {
        'id': 'foilness',
        'label': 'Foil',
        'sources': ('foilness',),
        'align': QtCore.Qt.AlignHCenter,
        'default_value': False,
    },
    {
        'id': 'count',
        'label': 'Count',
        'sources': ('count',),
        'align': QtCore.Qt.AlignRight,
        'default_value': 0,
    },
    {
        'id': 'price',
        'label': 'Price',
        'sources': ('price', 'currency',),
        'align': QtCore.Qt.AlignRight,
        'default_value': None,
    },
    {
        'id': 'tcg_price',
        'label': 'TCG',
        'sources': tuple(),
        'align': QtCore.Qt.AlignRight,
        'class': price.sources.TcgPlayer,
        'storage_id': 'tcg.prices',
        'resources': {
            'sets': getResourcePath('tcg-sets.json'),
        },
        'default_value': None,
    },
    {
        'id': 'source',
        'label': 'Source',
        'sources': ('source',),
        'align': QtCore.Qt.AlignLeft,
        'cursor': QtCore.Qt.PointingHandCursor,
        'default_value': '',
    },
]

VISITED_URLS = set()


class HyperlinkItemDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter, option, index):
        color = option.palette.link().color()
        if index.data(QtCore.Qt.ToolTipRole) in VISITED_URLS:
            color = option.palette.linkVisited().color()
        option.font.setUnderline(True)

        painter.save()
        painter.setFont(option.font)
        painter.setPen(color)
        painter.drawText(option.rect.adjusted(3, 0, 0, 0), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, index.data(QtCore.Qt.DisplayRole))
        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            url = index.data(QtCore.Qt.ToolTipRole)
            VISITED_URLS.add(url)
            if not url.startswith('http://'):
                url = 'http://{0}'.format(url)
            webbrowser.open(url)
            return True
        return False


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi('wizard.ui', self)

        self.foundCardsCount = 0
        self.wasSearchInProgress = False
        self.searchVersion = 0
        self.searchProgressQueue = queue.Queue()
        self.searchResults = multiprocessing.Queue()

        self.searchWorkers = {}
        self.searchProgressStats = {}

        self.priceStopEvent = multiprocessing.Event()
        self.priceRequests = multiprocessing.Queue()
        self.obtainedPrices = multiprocessing.Queue()
        self.priceWorkers = []
        for i, columnInfo in enumerate(SEARCH_RESULTS_TABLE_COLUMNS_INFO):
            if columnInfo['id'].endswith('price') and 'class' in columnInfo:
                sourceClass = columnInfo['class']
                storagePath = os.path.join(os.path.expanduser('~'), '.wots.{}.db'.format(columnInfo['storage_id']))
                process = multiprocessing.Process(
                    name=columnInfo['id'],
                    target=queryPriceSource,
                    args=(sourceClass, i, storagePath, columnInfo['resources'], self.priceRequests, self.obtainedPrices, self.priceStopEvent,),
                    daemon=True)
                self.priceWorkers.append(process)
                process.start()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.onTimerTick)
        self.timer.start(100)

        self.searchStopButton.setVisible(False)
        self.searchStopButton.clicked.connect(self.onSearchStopButtonClick)
        self.searchStartButton.setEnabled(False)
        self.searchStartButton.clicked.connect(self.searchCards)
        self.searchField.textChanged.connect(self.onSearchFieldTextChanged)
        self.searchField.returnPressed.connect(self.searchCards)

        cardsNamesSet = set()
        with codecs.open(getResourcePath('autocomplete.json'), 'r', 'utf-8') as fobj:
            cardsNamesMap = json.load(fobj)
            for namesList in cardsNamesMap.values():
                for name in namesList:
                    cardsNamesSet.add(name)

        with codecs.open(getResourcePath('database.json'), 'r', 'utf-8') as fobj:
            cardsInfo = json.load(fobj)

        self.searchResultsModel = CardsTableModel(cardsInfo, cardsNamesMap, SEARCH_RESULTS_TABLE_COLUMNS_INFO, self.searchResults, self.searchProgressQueue, self.priceRequests)
        self.searchResultsSortProxy = CardsSortProxy(SEARCH_RESULTS_TABLE_COLUMNS_INFO)
        self.searchResultsSortProxy.setSourceModel(self.searchResultsModel)
        self.searchResultsView.setModel(self.searchResultsSortProxy)
        self.searchResultsView.setItemDelegateForColumn(len(SEARCH_RESULTS_TABLE_COLUMNS_INFO) - 1, HyperlinkItemDelegate())
        self.searchResultsView.entered.connect(self.onSearchResultsCellMouseEnter)

        self.searchCompleter = QtWidgets.QCompleter(sorted(cardsNamesSet))
        self.searchCompleter.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.searchField.setCompleter(self.searchCompleter)

        header = self.searchResultsView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        # header.setMouseTracking(True)
        # header.entered.connect(self.onSearchResultsCellMouseEnter)

    def killWorkers(self, workers):
        for process in workers:
            if process.is_alive():
                os.kill(process.pid, signal.SIGTERM)

    def abort(self):
        self.priceStopEvent.set()
        self.killWorkers(self.searchWorkers.values())
        self.killWorkers(self.priceWorkers)

    def onSearchResultsCellMouseEnter(self, index):
        pass
        # cursor = SEARCH_RESULTS_TABLE_COLUMNS_INFO[index.column()].get('cursor', None)
        # if cursor:
        #     QtWidgets.QApplication.setOverrideCursor(cursor)
        # else:
        #     QtWidgets.QApplication.restoreOverrideCursor()

    def onSearchFieldTextChanged(self, text):
        self.searchStartButton.setEnabled(len(text) > 0)

    def onSearchStopButtonClick(self):
        self.searchStopEvent.set()
        self.searchStopButton.setEnabled(False)
        self.searchProgress.setValue(0)
        self.killWorkers(self.searchWorkers.values())
        self.searchWorkers = {}
        self.searchProgressStats = {}

    def onTimerTick(self):
        if self.searchResultsModel.canFetchMore(None):
            self.searchResultsModel.fetchMore(None)

        batchLength = 0
        self.searchResultsModel.beginUpdateCells()
        while not self.obtainedPrices.empty() and batchLength <= 10:
            row, column, priceInfo, searchVersion = self.obtainedPrices.get()
            if priceInfo and searchVersion == self.searchVersion:
                batchLength += 1
                self.searchResultsModel.updateCell(row, column, convertPrice(priceInfo))
        if batchLength > 0:
            self.searchResultsModel.endUpdateCells()

        self.updateSearchProgress()
        self.updateSearchControlsStatus()

    def isSearchInProgress(self):
        return any(process.is_alive() for process in self.searchWorkers.values())

    def updateSearchControlsStatus(self):
        searchInProgress = self.isSearchInProgress()
        self.searchField.setEnabled(not searchInProgress)
        self.searchStartButton.setVisible(not searchInProgress)
        self.searchStopButton.setVisible(searchInProgress)
        # if not searchInProgress and len(self.searchWorkers) > 0:
        #     import pprint
        #     pprint.pprint(self.searchProgressStats)

    def updateSearchProgress(self):
        currentProgress = self.searchProgress.value()
        newEnabledState = currentProgress != 0 and currentProgress != 100
        if self.searchProgress.isEnabled() != newEnabledState:
            self.searchProgress.setEnabled(newEnabledState)

        searchInProgress = self.isSearchInProgress()
        if self.searchResultsModel.cardCount > 0 and (self.foundCardsCount != self.searchResultsModel.cardCount or searchInProgress != self.wasSearchInProgress):
            message = '{} entries found.'.format(self.searchResultsModel.cardCount)
            if searchInProgress:
                message = '{} Searching for more...'.format(message)
            self.foundCardsCount = self.searchResultsModel.cardCount
            self.wasSearchInProgress = searchInProgress
            self.statusBar.showMessage(message)

        if len(self.searchWorkers) == 0 or currentProgress == 100:
            return

        while not self.searchProgressQueue.empty():
            engineId, foundCount, estimCount = self.searchProgressQueue.get()
            self.searchProgressStats[engineId] = (foundCount, estimCount)

        weightMultiplier = 1.0 / len(self.searchWorkers)
        newProgress = 0
        for engineId, worker in self.searchWorkers.items():
            engineProgress = 0
            if engineId in self.searchProgressStats:
                foundCount, estimCount = self.searchProgressStats[engineId]
                if estimCount == foundCount:
                    engineProgress = 100
                elif estimCount > 0:
                    engineProgress = foundCount / estimCount * 100
            elif not worker.is_alive():
                engineProgress = 100

            if engineProgress > 0:
                newProgress += min(100, engineProgress) * weightMultiplier

        newProgress = math.ceil(newProgress)
        if newProgress > currentProgress:
            self.searchProgress.setValue(newProgress)

    def searchCards(self):
        queryString = self.searchField.text()
        if not queryString:
            return
        queryString = queryString.strip()
        self.searchField.setText(queryString)
        queryString = card.utils.escape(queryString)

        while not self.priceRequests.empty():
            self.priceRequests.get_nowait()
        while not self.obtainedPrices.empty():
            self.obtainedPrices.get_nowait()
        while not self.searchProgressQueue.empty():
            self.searchProgressQueue.get_nowait()

        self.wasSearchInProgress = False
        self.foundCardsCount = 0
        self.searchVersion += 1
        self.searchWorkers = {}
        self.searchProgressStats = {}
        self.searchStopEvent = multiprocessing.Event()
        self.searchResultsModel.setCookie(self.searchVersion)
        self.searchResultsModel.clear()
        self.searchProgress.setValue(0)

        sourceClasses = card.sources.getCardSourceClasses()
        # sourceClasses = [card.sources.OfflineTestSource] * 10

        for i, sourceClass in enumerate(sourceClasses):
            engineId = ';'.join((str(sourceClass), str(i + 1), str(self.searchVersion)))
            process = multiprocessing.Process(
                name=str(sourceClass),
                target=queryCardSource,
                args=(engineId, sourceClass, queryString, self.searchResults, self.searchStopEvent, self.searchVersion,),
                daemon=True)
            process.start()
            self.searchWorkers[engineId] = process

        self.searchStopButton.setEnabled(True)
        self.updateSearchControlsStatus()


def queryCardSource(cardSourceId, cardSourceClass, queryString, resultsQueue, exitEvent, cookie):
    cardSource = cardSourceClass()
    for cardInfo in cardSource.query(queryString):
        if exitEvent.is_set():
            return
        resultsQueue.put((cardInfo, (cardSourceId, cardSource.getFoundCardsCount(), cardSource.getEstimatedCardsCount()), cookie,))


def queryPriceSource(priceSourceClass, sourceId, storagePath, resources, requestsQueue, resultsQueue, exitEvent):
    pricesQueue = multiprocessing.Queue()
    priceSource = priceSourceClass(pricesQueue, storagePath, resources)
    while True:
        if exitEvent.is_set():
            priceSource.terminate()
            return
        while not requestsQueue.empty():
            jobId, cookie, cardName, setId, language, foilness = requestsQueue.get_nowait()
            priceSource.queryPrice(cardName, setId, language, foilness, (jobId, cookie,))
        while not pricesQueue.empty():
            priceInfo, priceCookie = pricesQueue.get_nowait()
            jobId, cookie = priceCookie
            resultsQueue.put((jobId, sourceId, priceInfo, cookie,))


def convertPrice(priceInfo):
    amount, currency = priceInfo['price'], priceInfo['currency']
    original_amount, original_currency = amount, currency
    if currency is not None and amount is not None and currency != core.currency.RUR:
        roubles = currencyConverter.convert(currency, core.currency.RUR, amount)
        if roubles is not None:
            amount, currency = roubles, core.currency.RUR
    return {'amount': amount, 'currency': currency, 'original_amount': original_amount, 'original_currency': original_currency}


class CardsTableModel(QtCore.QAbstractTableModel):
    def __init__(self, cardsInfo, cardsNames, columnsInfo, dataQueue, statQueue, priceRequests):
        super().__init__()
        self.cardsNames = cardsNames
        self.columnsInfo = columnsInfo
        self.columnCount = len(columnsInfo)
        self.dataQueue = dataQueue
        self.statQueue = statQueue
        self.priceRequests = priceRequests
        self.dataTable = []
        self.cardCount = 0

        self.setsLanguages = {}
        self.cardIds = {}
        self.cardSets = {}
        for setId, setInfo in cardsInfo.items():
            setKey = card.sets.tryGetAbbreviation(setId)
            if setKey is not None:
                self.setsLanguages[setKey] = setInfo['languages']
                for cardKey, cardInfo in setInfo['cards'].items():
                    cardSets = self.cardSets.setdefault(cardKey, set())
                    cardSets.add(setKey)
                    if cardInfo[0] is not None:
                        self.cardIds.setdefault(setKey, {})[cardKey] = cardInfo[0]

    def setCookie(self, cookie):
        self.cookie = cookie

    def clear(self):
        self.beginRemoveRows(QtCore.QModelIndex(), 0, self.cardCount - 1)
        self.dataTable = []
        self.cardCount = 0
        self.endRemoveRows()

    def rowCount(self, parent):
        return self.cardCount

    def columnCount(self, parent):
        return self.columnCount

    def data(self, index, role):
        if index.isValid():
            columnIndex = index.column()
            columnInfo = self.columnsInfo[columnIndex]
            columnId = columnInfo['id']
            data = self.dataTable[index.row()][columnIndex]

            if role == QtCore.Qt.TextAlignmentRole:
                return columnInfo['align'] + QtCore.Qt.AlignVCenter

            if columnId == 'number':
                if role == QtCore.Qt.DisplayRole:
                    return str(data['id']).zfill(3) if data['id'] > 0 else None
            elif columnId == 'set':
                if role == QtCore.Qt.DisplayRole:
                    return data['set']
                elif role == QtCore.Qt.ToolTipRole:
                    setAbbrv = data['set']
                    return card.sets.getFullName(setAbbrv) if setAbbrv else None
            elif columnId == 'language':
                if role == QtCore.Qt.DisplayRole:
                    return data['language']
            elif columnId == 'name':
                if role == QtCore.Qt.DisplayRole:
                    return card.utils.unescape(data['name']['caption'])
                elif role == QtCore.Qt.ToolTipRole:
                    return data['name']['description']
            elif columnId == 'condition':
                if role == QtCore.Qt.DisplayRole:
                    return data['condition']
                elif role == QtCore.Qt.ToolTipRole:
                    return card.sources.getConditionHumanReadableString(data['condition'])
            elif columnId == 'foilness':
                if role == QtCore.Qt.DisplayRole:
                    return 'Foil' if data['foilness'] else None  # TODO image
            elif columnId == 'count':
                if role == QtCore.Qt.DisplayRole:
                    return int(data['count']) or ''
            elif columnId.endswith('price') and data and data['amount'] is not None:
                if role == QtCore.Qt.DisplayRole:
                    return core.currency.formatPrice(core.currency.roundPrice(data['amount']), data['currency'])
                elif role == QtCore.Qt.ToolTipRole:
                    return core.currency.formatPrice(data['original_amount'], data['original_currency']) if data['currency'] != data['original_currency'] else ''
            elif columnId == 'source':
                if role == QtCore.Qt.DisplayRole:
                    return data['source']['caption']
                elif role == QtCore.Qt.ToolTipRole:
                    return data['source']['url']

        return QtCore.QVariant()

    def headerData(self, section, orientation, role):
        result = QtCore.QVariant()
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            result = self.columnsInfo[section]['label']
        return result

    def canFetchMore(self, parent):
        return not self.dataQueue.empty()

    def fetchMore(self, parent):
        batch = []
        batchLength = 0
        while not self.dataQueue.empty() and batchLength <= 100:
            cardInfo, statInfo, cookie = self.dataQueue.get(block=False)
            if cookie == self.cookie:
                if cardInfo:
                    batch.append(cardInfo)
                    batchLength += 1
                self.statQueue.put(statInfo)
        self.beginInsertRows(QtCore.QModelIndex(), self.cardCount, self.cardCount + batchLength - 1)
        for cardInfo in batch:
            cardKey = card.utils.getNameKey(cardInfo['name']['caption'])
            if cardKey in self.cardsNames:
                newCardName = self.cardsNames[cardKey][0]
                cardInfo['name']['caption'] = newCardName
                cardKey = card.utils.getNameKey(newCardName)

            cardSets = self.cardSets.get(cardKey, None)
            if cardSets is not None and len(cardSets) == 1:
                newCardSet = card.sets.tryGetAbbreviation(list(cardSets)[0])
                if newCardSet is not None:
                    cardInfo['set'] = newCardSet

            if cardInfo['set']:
                setKey = card.sets.tryGetAbbreviation(cardInfo['set'])
                if setKey in self.cardIds:
                    newCardId = self.cardIds[setKey].get(cardKey, None)
                    if newCardId is not None:
                        cardInfo['id'] = newCardId

                if setKey in self.setsLanguages and len(self.setsLanguages[setKey]) == 1:
                    cardInfo['language'] = core.language.tryGetAbbreviation(self.setsLanguages[setKey][0])

            rowData = []
            for columnInfo in self.columnsInfo:
                columnData = {}
                for sourceId in columnInfo['sources']:
                    columnData[sourceId] = cardInfo.get(sourceId, None) or columnInfo['default_value']

                if columnInfo['id'].endswith('price') and len(columnData) > 0:
                    columnData = convertPrice(columnData)

                rowData.append(columnData)
            self.dataTable.append(rowData)

            if cardInfo.get('set'):
                self.priceRequests.put((len(self.dataTable) - 1, self.cookie, cardInfo['name']['caption'], cardInfo['set'], cardInfo['language'], cardInfo.get('foilness', False),))

        self.cardCount += batchLength
        self.endInsertRows()

    def beginUpdateCells(self):
        self.updatedCells = []

    def updateCell(self, row, column, value):
        self.dataTable[row][column] = value
        self.updatedCells.append((row, column))

    def endUpdateCells(self):
        # TODO Optimize
        for row, column in self.updatedCells:
            self.dataChanged.emit(self.index(row, column), self.index(row, column))


class CardsSortProxy(QtCore.QSortFilterProxyModel):
    def __init__(self, columnsInfo):
        super().__init__()
        self.columnsInfo = columnsInfo
        self.conditionsOrder = card.sources._CONDITIONS_ORDER

    def lessThan(self, aIndex, bIndex):
        model = self.sourceModel()
        columnIndex = aIndex.column()
        a = model.dataTable[aIndex.row()][columnIndex]
        b = model.dataTable[bIndex.row()][columnIndex]

        columnId = self.columnsInfo[columnIndex]['id']
        if columnId == 'number':
            return a['id'] < b['id']
        elif columnId == 'set':
            return a['set'] < b['set']
        elif columnId == 'language':
            return a['language'] < b['language']
        elif columnId == 'name':
            return a['name']['caption'] < b['name']['caption']
        elif columnId == 'condition':
            if not a['condition']:
                return True
            if not b['condition']:
                return False
            return self.conditionsOrder.index(a['condition']) < self.conditionsOrder.index(b['condition'])
        elif columnId == 'foilness':
            return a['foilness'] < b['foilness']
        elif columnId == 'count':
            return a['count'] < b['count']
        elif columnId.endswith('price'):
            if not a:
                return False
            if not b:
                return True
            am, bm = a['amount'], b['amount']
            if am is None:
                return False
            if bm is None:
                return True
            if a['currency'] != b['currency']:
                return a['currency'] < b['currency']
            return am < bm
        elif columnId == 'source':
            return a['source']['caption'] < b['source']['caption']
        return a < b


if __name__ == '__main__':
    try:
        if getattr(sys, 'frozen', False):
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()

        if platform.system() == 'Linux':
            # workaround for creating instances of QApplication in the child processes created by multiprocessing on Linux
            multiprocessing.set_start_method('spawn')

        multiprocessing.freeze_support()
        currencyConverter = core.currency.Converter()
        currencyConverter.update()
        application = QtWidgets.QApplication(sys.argv)
        window = MainWindow()
        window.show()
        try:
            sys.exit(application.exec_())
        finally:
            window.abort()
    except KeyboardInterrupt:
        pass
    finally:
        process = psutil.Process(os.getpid())
        for child in process.children(recursive=True):
            child.kill()
        process.kill()
