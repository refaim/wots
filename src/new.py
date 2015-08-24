import multiprocessing
import sys

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic

import card.sources
import card.utils
import core.currency


class QTableNumberWidgetItem(QtWidgets.QTableWidgetItem):
    def __init__(self, value):
        super().__init__()
        self.value = value or 0
        self.setData(QtCore.Qt.DisplayRole, self.getText())
        self.setData(QtCore.Qt.ToolTipRole, self.getToolTip())

    def getText(self):
        return str(self.value)

    def getToolTip(self):
        return None

    def __lt__(self, other):
        return self.value < other.value


class QTableCardIdWidgetItem(QTableNumberWidgetItem):
    def getText(self):
        return str(self.value).zfill(3) if self.value > 0 else ''


class QTableCardPriceWidgetItem(QTableNumberWidgetItem):
    def __init__(self, data):
        self.price, self.currency = data['price'], data['currency']
        self.roubles = self.price
        if self.currency is not None and self.price is not None and self.currency != core.currency.RUR:
            self.roubles = currencyConverter.convert(self.currency, core.currency.RUR, self.price)
        super().__init__(self.roubles)

    def getText(self):
        return core.currency.formatPrice(core.currency.roundPrice(self.roubles), core.currency.RUR)

    def getToolTip(self):
        return core.currency.formatPrice(self.price, self.currency) if self.currency != core.currency.RUR else None


class QTableCardConditionWidgetItem(QtWidgets.QTableWidgetItem):
    def __init__(self, condition):
        super().__init__(condition)
        self.condition = condition
        self.order = card.sources._CONDITIONS_ORDER

    def __lt__(self, other):
        return self.order.index(self.condition) < self.order.index(other.condition)


class QTableCardSetWidgetItem(QtWidgets.QTableWidgetItem):
    def __init__(self, setAbbrv):
        super().__init__(setAbbrv)
        if setAbbrv:
            self.setData(QtCore.Qt.ToolTipRole, card.sets.getFullName(setAbbrv))


class QTableCardNameWidgetItem(QtWidgets.QTableWidgetItem):
    def __init__(self, data):
        self.value = data['caption']
        super().__init__(card.utils.unescape(self.value))
        self.setData(QtCore.Qt.ToolTipRole, data['description'])


class QTableCardSourceWidgetItem(QtWidgets.QTableWidgetItem):
    def __init__(self, data):
        super().__init__()
        self.value = data['caption']

    def __lt__(self, other):
        return self.value < other.value


class QCardSourceHyperlinkLabel(QtWidgets.QLabel):
    def __init__(self, data):
        self.caption = data['caption']
        super().__init__('<a href="{}">{}</a>'.format(data['url'], self.caption))
        self.setOpenExternalLinks(True)


class QTableCardFoilnessWidgetItem(QtWidgets.QLabel):
    def __init__(self, foil):
        super().__init__('Foil' if foil else None)


class CardsTableModel(QtCore.QAbstractTableModel):
    def data(self, index, role):
        row = index.row()
        column = index.column()


SEARCH_RESULTS_TABLE_COLUMNS_INFO = [
    {
        'label': '#',
        'sources': ('id',),
        'align': QtCore.Qt.AlignRight,
        'item': QTableCardIdWidgetItem,
    },
    {
        'label': 'Set',
        'sources': ('set',),
        'align': QtCore.Qt.AlignHCenter,
        'item': QTableCardSetWidgetItem,
    },
    {
        'label': 'LNG',
        'sources': ('language',),
        'align': QtCore.Qt.AlignHCenter,
        'item': QtWidgets.QTableWidgetItem,
    },
    {
        'label': 'Name',
        'sources': ('name',),
        'align': QtCore.Qt.AlignLeft,
        'item': QTableCardNameWidgetItem,
    },
    {
        'label': 'CND',
        'sources': ('condition',),
        'align': QtCore.Qt.AlignHCenter,
        'item': QTableCardConditionWidgetItem,
    },
    {
        'label': 'Foil',
        'sources': ('foilness',),
        'align': QtCore.Qt.AlignHCenter,
    },
    {
        'label': 'Count',
        'sources': ('count',),
        'align': QtCore.Qt.AlignRight,
        'item': QTableNumberWidgetItem,
    },
    {
        'label': 'Price',
        'sources': ('price', 'currency',),
        'align': QtCore.Qt.AlignRight,
        'item': QTableCardPriceWidgetItem,
    },
    # {
    #     'id': 'tcg',
    #     'label': 'TCG',
    #     'horz_alignment': QtCore.Qt.AlignRight,
    #     'formatter': lambda x: formatRoubles(x.get('roubles')) if x else '',
    #     'tooltipper': lambda x: x.get('original') if x else ''
    # },
    {
        'label': 'Source',
        'sources': ('source',),
        'align': QtCore.Qt.AlignLeft,
        'item': QTableCardSourceWidgetItem,
        'widget': QCardSourceHyperlinkLabel,
    },
]


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi('wizard.ui', self)

        self.searchVersion = 0
        self.searchWorkers = []
        self.searchResultsQueue = multiprocessing.Queue()

        self.obtainedPrices = multiprocessing.Queue()
        self.priceRequests = multiprocessing.Queue()
        # self.priceRetrieverStopEvent = threading.Event()
        # self.priceRetriever = threading.Thread(name='Prices', target=priceRetriever, args=(self.priceRequests, self, self.priceRetrieverStopEvent,))
        # self.priceRetriever.daemon = True
        # self.priceRetriever.start()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.onTimerTick)
        self.timer.start(300)

        self.searchStopButton.setVisible(False)
        self.searchStopButton.clicked.connect(self.onSearchStopButtonClick)
        self.searchStartButton.setEnabled(False)
        self.searchStartButton.clicked.connect(self.searchCards)
        self.searchField.textChanged.connect(self.onSearchFieldTextChanged)
        self.searchField.returnPressed.connect(self.searchCards)

        self.resultsTable.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        # self.resultsTable.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.resultsTable.setColumnCount(len(SEARCH_RESULTS_TABLE_COLUMNS_INFO))
        for i, columnInfo in enumerate(SEARCH_RESULTS_TABLE_COLUMNS_INFO):
            self.resultsTable.setHorizontalHeaderItem(i, QtWidgets.QTableWidgetItem(columnInfo['label']))

    def onSearchFieldTextChanged(self, text):
        self.searchStartButton.setEnabled(len(text) > 0)

    def onSearchStopButtonClick(self):
        self.searchStopEvent.set()
        self.searchStopButton.setEnabled(False)
        self.searchWorkers = []

    def onTimerTick(self):
        foundCount = 0
        self.resultsTable.setSortingEnabled(False)
        while not self.searchResultsQueue.empty() and foundCount <= 10:
            foundCount += 1
            cardInfo, searchVersion = self.searchResultsQueue.get(block=False)
            if searchVersion == self.searchVersion:
                self.resultsTable.setRowCount(self.resultsTable.rowCount() + 1)  # TODO Optimize
                for columnIndex in range(self.resultsTable.columnCount()):
                    rowIndex = self.resultsTable.rowCount() - 1
                    columnInfo = SEARCH_RESULTS_TABLE_COLUMNS_INFO[columnIndex]
                    dataSources = columnInfo['sources']
                    if len(dataSources) > 1:
                        cellData = {}
                        for fieldId in dataSources:
                            cellData[fieldId] = cardInfo.get(fieldId, None)
                    else:
                        cellData = cardInfo.get(dataSources[0], None)
                    if 'widget' in columnInfo:
                        widget = columnInfo['widget'](cellData)
                        self.resultsTable.setCellWidget(rowIndex, columnIndex, widget)
                    if 'item' in columnInfo:
                        item = columnInfo['item'](cellData)
                        item.setTextAlignment(columnInfo['align'] | QtCore.Qt.AlignVCenter)
                        self.resultsTable.setItem(rowIndex, columnIndex, item)
        self.resultsTable.setSortingEnabled(True)
                # if cardInfo.get('set'):
                #     # TODO Replace 0 with proper jobId
                #     self.priceRequests.put((0, self.searchVersion, cardInfo['name'], cardInfo['set'], cardInfo['language'], cardInfo.get('foilness', False),))

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

        self.searchVersion += 1
        self.searchWorkers = []
        self.searchStopEvent = multiprocessing.Event()
        self.resultsTable.setRowCount(0)

        sourceClasses = card.sources.getCardSourceClasses()
        for sourceClass in sourceClasses:
            instance = sourceClass()
            process = multiprocessing.Process(
                name=instance.getTitle(),
                target=queryCardSource,
                args=(instance, queryString, self.searchResultsQueue, self.searchStopEvent, self.searchVersion,),
                daemon=True)
            process.start()
            self.searchWorkers.append(process)

        self.searchStopButton.setEnabled(True)
        self.updateSearchControlsStatus()
        # rowCount = self.resultsGrid.GetNumberRows()
        # if rowCount > 0:
        #     self.resultsGrid.ClearGrid()
        #     self.resultsGrid.DeleteRows(pos=0, numRows=rowCount)

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


# class SearchResultsTableModel(QtCore.QAbstractTableModel):
#     def __init__(self, columnsInfo):
#         super().__init__()
#         self.data = []
#         self.columnsInfo = columnsInfo

#     def data(self, index, role):
#         result = QtCore.QVariant()
#         if index.isValid() and role == QtCore.Qt.DisplayRole:
#             result = self.data[index.row()][index.column()]
#         return result

#     def rowCount(self, parent):
#         return len(self.data)

#     def columnCount(self, parent):
#         return len(self.columnsInfo)

#     def headerData(self, section, orientation, role):
#         result = QtCore.QVariant()
#         if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
#             result = self.columnsInfo[section]['label']
#         return result

#     def insertRows(self, row, count, parent):
#         self.beginInsertRows(parent, row, row + count - 1)
#         tableItems.insert(tableIndex(row, 0), cc * count, 0);
#         self.endInsertRows()
#         return True

# def processPriceRequests(processor, requests, results, exitEvent):
#     while not exitEvent.is_set():
#         try:
#             jobId, cookie, cardName, setId, language, foilness = requests.get(block=False)
#             results.put((jobId, processor.queryPrice(cardName, setId, language, foilness), cookie))
#         except Queue.Empty:
#             pass


# def priceRetriever(taskQueue, wxEventBus, exitEvent):
#     requests = multiprocessing.Queue()
#     results = multiprocessing.Queue()
#     workers = []
#     terminators = []
#     for sourceClass in price.sources.getPriceSourceClasses():
#         source = sourceClass()
#         event = multiprocessing.Event()
#         terminators.append(event)
#         workers.append(multiprocessing.Process(name=source.getTitle(), target=processPriceRequests, args=(source, requests, results, event,)))
#     for process in workers:
#         process.daemon = True
#         process.start()
#     while not exitEvent.is_set():
#         try:
#             while not taskQueue.empty():
#                 requests.put(taskQueue.get(block=False))
#             while not results.empty():
#                 jobId, priceInfo, cookie = results.get(block=False)
#                 wx.PostEvent(wxEventBus, PriceObtainedEvent(jobId, priceInfo, cookie))
#         except Queue.Empty:
#             pass
#     for terminator in terminators:
#         terminator.set()


if __name__ == '__main__':
    currencyConverter = core.currency.Converter()
    currencyConverter.update()
    application = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(application.exec_())
