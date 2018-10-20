import logging
import math
import os
import sys
from functools import partial
from io import StringIO
from multiprocessing import Event as MpEvent
from multiprocessing import Process as MpProcess
from multiprocessing import Queue as MpQueue
from multiprocessing import freeze_support as mp_freeze_support, set_start_method as mp_set_start_method
from queue import Queue as SpQueue
from signal import SIGTERM
from threading import Thread
from typing import Callable, ClassVar
from webbrowser import open as open_browser

import dotenv
import psutil
import raven
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic

import version
from card.components import SetOracle, ConditionOracle, LanguageOracle
from card.fixer import CardsFixer
from card.sources import getCardSourceClasses, CardSource
from card.utils import CardUtils
from core.components.cbr import CentralBankApiClient
from core.utils import Currency, ILogger, MultiprocessingLogger, OsUtils, StringUtils
from core.utils import load_json_resource, get_project_root, get_resource_path

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
    # {
    #     'id': 'tcg_price',
    #     'label': 'TCG',
    #     'sources': tuple(),
    #     'align': QtCore.Qt.AlignRight,
    #     'class': price.sources.TcgPlayer,
    #     'storage_id': 'tcg.prices',
    #     'resources': {
    #         'sets': getResourcePath('tcg-sets.json'),
    #     },
    #     'default_value': None,
    # },
    {
        'id': 'source',
        'label': 'Source',
        'sources': ('source',),
        'align': QtCore.Qt.AlignLeft,
        'cursor': QtCore.Qt.PointingHandCursor,
        'hyperlink': True,
        'default_value': '',
    },
    {
        'id': 'description',
        'label': 'Description',
        'sources': ('name',),
        'align': QtCore.Qt.AlignLeft,
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
            url = url.replace('https://', 'http://')
            if not url.startswith('http://'):
                url = 'http://{0}'.format(url)
            open_browser(url)
            return True
        return False


class Container(object):
    def __init__(self):
        self.__data = {}

    def has(self, cls: ClassVar):
        return cls in self.__data

    def get(self, cls: ClassVar):
        return self.__data[cls]

    def put(self, value: object, cls: ClassVar = None) -> None:
        if cls is None:
            cls = value.__class__
        self.__data[cls] = value


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, logger: ILogger):
        super().__init__()

        self.logger = logger
        self.container = Container()

        cbr = Thread(target=setupCentralBank, args=(self.logger.get_child('cb'), gSentry, self.container))
        cbr.daemon = True
        cbr.start()

        uic.loadUi(get_resource_path('wizard.ui'), self)
        self.setWindowTitle(self.windowTitle().format(version=version.VERSION))

        self.foundCardsCount = 0
        self.wasSearchInProgress = False
        self.searchVersion = 0
        self.searchProgressQueue = SpQueue()
        self.searchResults = MpQueue()

        self.searchWorkers = {}
        self.searchProgressStats = {}

        self.priceStopEvent = MpEvent()
        self.priceRequests = MpQueue()
        self.obtainedPrices = MpQueue()
        self.priceWorkers = []
        for i, columnInfo in enumerate(SEARCH_RESULTS_TABLE_COLUMNS_INFO):
            if columnInfo['id'].endswith('price') and 'class' in columnInfo:
                sourceClass = columnInfo['class']
                storagePath = os.path.join(os.path.expanduser('~'), '.wots.{}.db'.format(columnInfo['storage_id']))
                # noinspection PyArgumentList
                process = MpProcess(
                    name=columnInfo['id'],
                    target=partial(mpEntryPoint, queryPriceSource),
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

        cardsInfo = load_json_resource('database.json')
        cardsNamesMap = load_json_resource('completion_map.json')
        cardsNamesSet = load_json_resource('completion_set.json')

        self.container.put(LanguageOracle(self.logger, thorough=False))
        self.container.put(SetOracle(self.logger, thorough=False))
        self.container.put(ConditionOracle(self.logger, thorough=False))
        self.container.put(CardsFixer(cardsInfo, cardsNamesMap, self.container.get(SetOracle), self.container.get(LanguageOracle), self.logger.get_child('fixer')))
        self.searchResultsModel = CardsTableModel(SEARCH_RESULTS_TABLE_COLUMNS_INFO, self.searchResults, self.searchProgressQueue, self.priceRequests, self.container)
        self.searchResultsSortProxy = CardsSortProxy(SEARCH_RESULTS_TABLE_COLUMNS_INFO)
        self.searchResultsSortProxy.setSourceModel(self.searchResultsModel)
        self.searchResultsView.setModel(self.searchResultsSortProxy)

        for i, columnInfo in enumerate(SEARCH_RESULTS_TABLE_COLUMNS_INFO):
            if columnInfo.get('hyperlink'):
                self.searchResultsView.setItemDelegateForColumn(i, HyperlinkItemDelegate())

        self.searchResultsView.entered.connect(self.onSearchResultsCellMouseEnter)

        self.searchCompleter = QtWidgets.QCompleter(sorted(cardsNamesSet))
        self.searchCompleter.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.searchCompleter.setFilterMode(QtCore.Qt.MatchContains)
        self.searchField.setCompleter(self.searchCompleter)

        header = self.searchResultsView.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        # header.setMouseTracking(True)
        # header.entered.connect(self.onSearchResultsCellMouseEnter)

    def killWorkers(self, workers):
        for process in workers:
            if process.is_alive():
                os.kill(process.pid, SIGTERM)

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
        while not self.obtainedPrices.empty() and batchLength <= 10:
            row, column, priceInfo, searchVersion = self.obtainedPrices.get()
            if priceInfo and searchVersion == self.searchVersion:
                if batchLength == 0:
                    self.searchResultsModel.beginUpdateCells()
                batchLength += 1
                self.searchResultsModel.updateCell(row, column, self.searchResultsModel.convertPrice(priceInfo))
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

    def updateSearchProgress(self):
        currentProgress = self.searchProgress.value()
        newEnabledState = currentProgress != 0 and currentProgress != 100
        if self.searchProgress.isEnabled() != newEnabledState:
            self.searchProgress.setEnabled(newEnabledState)

        searchInProgress = self.isSearchInProgress()
        message = None
        if self.searchResultsModel.cardCount == 0:
            message = 'Searching...'
        elif self.foundCardsCount != self.searchResultsModel.cardCount or searchInProgress != self.wasSearchInProgress:
            message = '{} entries found.'.format(self.searchResultsModel.cardCount)
            if searchInProgress:
                message = '{} Searching for more...'.format(message)
            self.foundCardsCount = self.searchResultsModel.cardCount
            self.wasSearchInProgress = searchInProgress
        if message is not None:
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
        queryString = CardUtils.unquote(CardUtils.utf2std(queryString))

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
        self.searchStopEvent = MpEvent()
        self.searchResultsModel.setCookie(self.searchVersion)
        self.searchResultsModel.clear()
        self.searchProgress.setValue(0)

        sourceClasses = getCardSourceClasses()
        # sourceClasses = [card.sources.OfflineTestSource] * 10

        for i, sourceClass in enumerate(sourceClasses):
            engineId = ';'.join((str(sourceClass), str(i + 1), str(self.searchVersion)))
            process = MpProcess(name=str(sourceClass), target=partial(mpEntryPoint, queryCardSource),
                args=(engineId, sourceClass, queryString, self.searchResults, self.logger, self.searchStopEvent, self.searchVersion))
            process.daemon = True
            process.start()
            self.searchWorkers[engineId] = process

        self.searchStopButton.setEnabled(True)
        self.updateSearchControlsStatus()


def mpEntryPoint(original: Callable, *args, **kwargs) -> None:
    sentry = raven.Client(os.getenv('SENTRY_DSN'))
    try:
        original(*args, **kwargs)
    except KeyboardInterrupt:
        return
    except Exception:
        sentry.captureException()
        raise


def queryCardSource(cardSourceId: int, instanceClass, queryString: str, resultsQueue: MpQueue, logger: ILogger, exitEvent: MpEvent, cookie):
    cardSource: CardSource = instanceClass(logger)
    for cardInfo in cardSource.query(queryString):
        if exitEvent.is_set():
            return
        resultsQueue.put((cardInfo, (cardSourceId, cardSource.getFoundCardsCount(), cardSource.getEstimatedCardsCount()), cookie,))


def queryPriceSource(priceSourceClass, sourceId, storagePath, resources, requestsQueue, resultsQueue, exitEvent):
    pricesQueue = MpQueue()
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


def setupCentralBank(logger: ILogger, sentry: raven.Client, container: Container) -> None:
    client = CentralBankApiClient(logger, sentry)
    client.update_rates()
    container.put(client)


class CardsTableModel(QtCore.QAbstractTableModel):
    def __init__(self, columnsInfo, dataQueue, statQueue, priceRequests, container: Container):
        super().__init__()
        self.columnsInfo = columnsInfo
        self.columnCount = len(columnsInfo)
        self.dataQueue = dataQueue
        self.statQueue = statQueue
        self.priceRequests = priceRequests
        self.container = container
        self.cardsFixer = self.container.get(CardsFixer)
        self.langOracle = self.container.get(LanguageOracle)
        self.setOracle = self.container.get(SetOracle)
        self.conditionOracle = self.container.get(ConditionOracle)
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
                setAbbrv = data['set']
                if role == QtCore.Qt.DisplayRole:
                    return setAbbrv
                elif role == QtCore.Qt.ToolTipRole:
                    return self.setOracle.get_name(setAbbrv) if setAbbrv else None
            elif columnId == 'language':
                lang = data['language']
                if role == QtCore.Qt.DisplayRole:
                    return lang
                elif role == QtCore.Qt.ToolTipRole:
                    return self.langOracle.get_name(lang) if lang else None
            elif columnId == 'name':
                if role == QtCore.Qt.DisplayRole:
                    return CardUtils.std2utf(data['name']['caption'])
            elif columnId == 'condition':
                condition = data['condition']
                if role == QtCore.Qt.DisplayRole:
                    return condition
                elif role == QtCore.Qt.ToolTipRole:
                    return self.conditionOracle.get_name(condition) if condition else None
            elif columnId == 'foilness':
                if role == QtCore.Qt.DisplayRole:
                    return 'Foil' if data['foilness'] else None  # TODO image
            elif columnId == 'count':
                if role == QtCore.Qt.DisplayRole:
                    if isinstance(data['count'], bool) and data['count'] is True:
                        return '1+'
                    return int(data['count']) or ''
            elif columnId.endswith('price') and data and data['amount'] is not None:
                if role == QtCore.Qt.DisplayRole:
                    return StringUtils.format_money(int(data['amount']), data['currency'])
                elif role == QtCore.Qt.ToolTipRole:
                    return StringUtils.format_money(data['original_amount'], data['original_currency']) if data['currency'] != data['original_currency'] else ''
            elif columnId == 'source':
                if role == QtCore.Qt.DisplayRole:
                    return data['source']['caption']
                elif role == QtCore.Qt.ToolTipRole:
                    return data['source']['url']
            elif columnId == 'description':
                if role == QtCore.Qt.DisplayRole:
                    return data['name']['description']

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
        for rawCardInfo in batch:
            cardInfo = self.cardsFixer.fixCardInfo(rawCardInfo)

            rowData = []
            for columnInfo in self.columnsInfo:
                columnData = {}
                for sourceId in columnInfo['sources']:
                    columnData[sourceId] = cardInfo.get(sourceId, None) or columnInfo['default_value']

                if columnInfo['id'].endswith('price') and len(columnData) > 0:
                    columnData = self.convertPrice(columnData)

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

    def convertPrice(self, priceInfo):
        amount, currency = priceInfo['price'], priceInfo['currency']
        original_amount, original_currency = amount, currency
        if currency is not None and amount is not None and currency != Currency.RUR and self.container.has(CentralBankApiClient):
            cbr: CentralBankApiClient = self.container.get(CentralBankApiClient)
            roubles = cbr.exchange(amount, currency, Currency.RUR)
            if roubles is not None:
                amount, currency = roubles, Currency.RUR
        return {'amount': amount, 'currency': currency, 'original_amount': original_amount, 'original_currency': original_currency}



class CardsSortProxy(QtCore.QSortFilterProxyModel):
    def __init__(self, columnsInfo):
        super().__init__()
        self.columnsInfo = columnsInfo
        self.conditionsOrder = ConditionOracle.get_order()

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
            ac = a['count']
            bc = b['count']
            ap = isinstance(ac, bool) and ac is True
            bp = isinstance(bc, bool) and bc is True
            ai = int(ac) if ac is not None else 0
            bi = int(bc) if bc is not None else 0
            if ai == bi and ap != bp:
                return bp
            return ai < bi
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
        elif columnId == 'description':
            return a['name']['description'] < b['name']['description']
        return a < b


def __get_main_process():
    return psutil.Process(os.getpid())


def __kill_children_processes():
    for child in __get_main_process().children(recursive=True):
        try:
            child.kill()
        except psutil.NoSuchProcess:
            pass


def __catch_exceptions(hook, type_, value, traceback):
    __kill_children_processes()
    sys.excepthook = hook
    sys.excepthook(type_, value, traceback)


def setupLogging() -> ILogger:
    logsQueue = MpQueue()
    logger = MultiprocessingLogger('', logsQueue)
    logsThread = Thread(target=__handleIncomingLogs, args=(logsQueue,))
    logsThread.daemon = True
    logsThread.start()
    return logger


def __handleIncomingLogs(logsQueue: MpQueue) -> None:
    loggers = {}
    while True:
        name, level, message, args, kwargs = logsQueue.get()
        if name not in loggers:
            loggers[name] = logging.getLogger(name)
        loggers[name].log(level, message, *args, *kwargs)


if __name__ == '__main__':
    gRequiredVersion = (3, 6, 5)
    if sys.version_info < gRequiredVersion:
        print('Python {}.{}.{}+ required'.format(*gRequiredVersion), file=sys.stderr)
        sys.exit(1)

    mp_freeze_support()
    dotenv.load_dotenv(os.path.join(get_project_root(), '.env'))
    gSentry = raven.Client(os.getenv('SENTRY_DSN'))
    sys.excepthook = partial(__catch_exceptions, sys.excepthook)
    try:
        if getattr(sys, 'frozen', False):
            sys.stdout = StringIO()
            sys.stderr = StringIO()

        if OsUtils.is_linux():
            # workaround for creating instances of QApplication in the child processes created by multiprocessing on Linux
            mp_set_start_method('spawn')

        gRootLogger = setupLogging()
        gApplication = QtWidgets.QApplication(sys.argv)
        gWindow = MainWindow(gRootLogger)
        try:
            gWindow.show()
            sys.exit(gApplication.exec_())
        finally:
            gWindow.abort()
    except SystemExit:
        pass
    except Exception:
        gSentry.captureException()
        raise
    finally:
        __kill_children_processes()
