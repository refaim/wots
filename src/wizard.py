import multiprocessing
import os
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


class HypelinkItemDelegate(QtWidgets.QStyledItemDelegate):
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
                process = multiprocessing.Process(
                    name=columnInfo['id'],
                    target=queryPriceSource,
                    args=(sourceClass, i, self.priceRequests, self.obtainedPrices, self.priceStopEvent,),
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

        self.searchResultsModel = CardsTableModel(SEARCH_RESULTS_TABLE_COLUMNS_INFO, self.searchResults, self.searchProgressQueue, self.priceRequests)
        self.searchResultsSortProxy = CardsSortProxy(SEARCH_RESULTS_TABLE_COLUMNS_INFO)
        self.searchResultsSortProxy.setSourceModel(self.searchResultsModel)
        self.searchResultsView.setModel(self.searchResultsSortProxy)
        self.searchResultsView.setItemDelegateForColumn(len(SEARCH_RESULTS_TABLE_COLUMNS_INFO) - 1, HypelinkItemDelegate())
        self.searchResultsView.entered.connect(self.onSearchResultsCellMouseEnter)

        header = self.searchResultsView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        # header.setMouseTracking(True)
        # header.entered.connect(self.onSearchResultsCellMouseEnter)

    def abort(self):
        self.priceStopEvent.set()
        for process in list(self.searchWorkers.values()) + self.priceWorkers:
            if process.is_alive():
                os.kill(process.pid, signal.SIGTERM)

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
        self.searchWorkers = {}
        self.searchProgressStats = {}

    def onTimerTick(self):
        if self.searchResultsModel.canFetchMore(None):
            self.searchResultsModel.fetchMore(None)

        while not self.obtainedPrices.empty():
            row, column, priceInfo, searchVersion = self.obtainedPrices.get()
            if priceInfo and searchVersion == self.searchVersion:
                self.searchResultsModel.updateCell(row, column, convertPrice(priceInfo))

        self.updateSearchProgress()
        self.updateSearchControlsStatus()

    def updateSearchControlsStatus(self):
        searchInProgress = any(process.is_alive() for process in self.searchWorkers.values())
        self.searchField.setEnabled(not searchInProgress)
        self.searchStartButton.setVisible(not searchInProgress)
        self.searchStopButton.setVisible(searchInProgress)
        if not searchInProgress and len(self.searchWorkers) > 0 and self.searchProgress.value() == 0:
            self.searchProgress.setValue(100)

    def updateSearchProgress(self):
        if len(self.searchWorkers) == 0:
            return

        while not self.searchProgressQueue.empty():
            engineId, foundCount, estimCount = self.searchProgressQueue.get()
            self.searchProgressStats[engineId] = (foundCount, estimCount)

        weightMultiplier = 1.0 / len(self.searchWorkers)
        currentProgress = 0
        for engineId, worker in self.searchWorkers.items():
            engineProgress = 0
            if engineId in self.searchProgressStats:
                foundCount, estimCount = self.searchProgressStats[engineId]
                if estimCount > 0:
                    engineProgress = foundCount / estimCount * 100
            elif not worker.is_alive():
                engineProgress = 100

            if engineProgress > 0:
                currentProgress += min(100, engineProgress) * weightMultiplier

        if currentProgress > self.searchProgress.value():
            self.searchProgress.setValue(currentProgress)

    def searchCards(self):
        queryString = self.searchField.text()
        if not queryString:
            return
        queryString = card.utils.escape(queryString)

        while not self.priceRequests.empty():
            self.priceRequests.get_nowait()
        while not self.obtainedPrices.empty():
            self.obtainedPrices.get_nowait()
        while not self.searchProgressQueue.empty():
            self.searchProgressQueue.get_nowait()

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
            engine = sourceClass()
            engineId = ';'.join((engine.getTitle(), str(i + 1), str(self.searchVersion)))
            process = multiprocessing.Process(
                name=engine.getTitle(),
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


def queryPriceSource(priceSourceClass, sourceId, requestsQueue, resultsQueue, exitEvent):
    pricesQueue = multiprocessing.Queue()
    priceSource = priceSourceClass(pricesQueue)
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
    def __init__(self, columnsInfo, dataQueue, statQueue, priceRequests):
        super().__init__()
        self.columnsInfo = columnsInfo
        self.colunmCount = len(columnsInfo)
        self.dataQueue = dataQueue
        self.statQueue = statQueue
        self.priceRequests = priceRequests
        self.dataTable = []
        self.cardCount = 0

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
        return self.colunmCount

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

    def updateCell(self, row, column, value):
        self.dataTable[row][column] = value
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


class CardsComplete(QtWidgets.QCompleter):
    def setCompletionPrefix(self, prefix):
        pass


if __name__ == '__main__':
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
