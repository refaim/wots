import multiprocessing
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
        self.searchWorkers = []
        self.searchResults = multiprocessing.Queue()

        self.priceRequests = multiprocessing.Queue()
        self.obtainedPrices = multiprocessing.Queue()
        for i, columnInfo in enumerate(SEARCH_RESULTS_TABLE_COLUMNS_INFO):
            if columnInfo['id'].endswith('price') and 'class' in columnInfo:
                priceSource = columnInfo['class']()
                process = multiprocessing.Process(
                    name=priceSource.getTitle(),
                    target=queryPriceSource,
                    args=(priceSource, i, self.priceRequests, self.obtainedPrices,),
                    daemon=True)
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

        self.searchResultsModel = CardsTableModel(SEARCH_RESULTS_TABLE_COLUMNS_INFO, self.searchResults, self.priceRequests)
        self.searchResultsSortProxy = CardsSortProxy(SEARCH_RESULTS_TABLE_COLUMNS_INFO)
        self.searchResultsSortProxy.setSourceModel(self.searchResultsModel)
        self.searchResultsView.setModel(self.searchResultsSortProxy)
        self.searchResultsView.setItemDelegateForColumn(len(SEARCH_RESULTS_TABLE_COLUMNS_INFO) - 1, HypelinkItemDelegate())
        self.searchResultsView.entered.connect(self.onSearchResultsCellMouseEnter)

        header = self.searchResultsView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        # header.setMouseTracking(True)
        # header.entered.connect(self.onSearchResultsCellMouseEnter)

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
        self.searchWorkers = []

    def onTimerTick(self):
        if self.searchResultsModel.canFetchMore(None):
            self.searchResultsModel.fetchMore(None)
        while not self.obtainedPrices.empty():
            row, column, priceInfo, searchVersion = self.obtainedPrices.get()
            if priceInfo and searchVersion == self.searchVersion:
                self.searchResultsModel.updateCell(row, column, convertPrice(priceInfo))
        self.updateSearchControlsStatus()

    def updateSearchControlsStatus(self):
        searchInProgress = any(process.is_alive() for process in self.searchWorkers)
        self.searchField.setEnabled(not searchInProgress)
        self.searchStartButton.setVisible(not searchInProgress)
        self.searchStopButton.setVisible(searchInProgress)

    def searchCards(self):
        queryString = self.searchField.text()
        if not queryString:
            return
        queryString = card.utils.escape(queryString)

        while not self.priceRequests.empty():
            self.priceRequests.get_nowait()
        while not self.obtainedPrices.empty():
            self.obtainedPrices.get_nowait()

        self.searchVersion += 1
        self.searchWorkers = []
        self.searchStopEvent = multiprocessing.Event()
        self.searchResultsModel.setCookie(self.searchVersion)
        self.searchResultsModel.clear()

        sourceClasses = card.sources.getCardSourceClasses()
        for sourceClass in sourceClasses:
            instance = sourceClass()
            process = multiprocessing.Process(
                name=instance.getTitle(),
                target=queryCardSource,
                args=(instance, queryString, self.searchResults, self.searchStopEvent, self.searchVersion,),
                daemon=True)
            process.start()
            self.searchWorkers.append(process)

        self.searchStopButton.setEnabled(True)
        self.updateSearchControlsStatus()

    def packPrice(self, price, currency):
        result = {}
        roubles = price
        if currency is not None and price is not None and currency != core.currency.RUR:
            roubles = self.currencyConverter.convert(currency, core.currency.RUR, price)
            result['original'] = core.currency.formatPrice(price, currency)
        result['roubles'] = roubles
        return result


def queryCardSource(cardSource, queryString, resultsQueue, exitEvent, cookie):
    for cardInfo in cardSource.query(queryString):
        if exitEvent.is_set():
            return
        resultsQueue.put((cardInfo, cookie,))


def queryPriceSource(priceSource, sourceId, requestsQueue, resultsQueue):
    while True:
        jobId, cookie, cardName, setId, language, foilness = requestsQueue.get()
        resultsQueue.put((jobId, sourceId, priceSource.queryPrice(cardName, setId, language, foilness), cookie))


def convertPrice(priceInfo):
    price, currency = priceInfo['price'], priceInfo['currency']
    roubles = price
    if currency is not None and price is not None and currency != core.currency.RUR:
        roubles = currencyConverter.convert(currency, core.currency.RUR, price)
    return {'price': price, 'currency': currency, 'roubles': roubles}


class CardsTableModel(QtCore.QAbstractTableModel):
    def __init__(self, columnsInfo, dataQueue, priceRequests):
        super().__init__()
        self.columnsInfo = columnsInfo
        self.colunmCount = len(columnsInfo)
        self.dataQueue = dataQueue
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
            elif columnId == 'foilness':
                if role == QtCore.Qt.DisplayRole:
                    return 'Foil' if data['foilness'] else None  # TODO image
            elif columnId == 'count':
                if role == QtCore.Qt.DisplayRole:
                    return int(data['count']) or ''
            elif columnId.endswith('price') and data:
                if role == QtCore.Qt.DisplayRole:
                    return core.currency.formatPrice(core.currency.roundPrice(data['roubles']), core.currency.RUR)
                elif role == QtCore.Qt.ToolTipRole:
                    return core.currency.formatPrice(data['price'], data['currency']) if data['currency'] != core.currency.RUR else ''
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
            cardInfo, cookie = self.dataQueue.get(block=False)
            if cookie == self.cookie:
                batch.append(cardInfo)
                batchLength += 1
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
                return True
            if not b:
                return False
            return a['roubles'] < b['roubles']
        elif columnId == 'source':
            return a['source']['caption'] < b['source']['caption']
        return a < b


if __name__ == '__main__':
    multiprocessing.freeze_support()
    currencyConverter = core.currency.Converter()
    currencyConverter.update()
    application = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(application.exec_())