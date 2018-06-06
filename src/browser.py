# import codecs
# import functools
# import queue
# import sys
# import threading
# import time
# import lxml.html

# from PyQt5 import QtCore
# from PyQt5 import QtWebKitWidgets
# from PyQt5 import QtWidgets

# class WebBrowser(object):
#     def __init__(self, parentId):
#         self._requests = queue.Queue()
#         self._results = queue.Queue()
#         self._renderThread = threading.Thread(name='{}-render-thread'.format(parentId), target=renderThread, args=(self._requests, self._results,), daemon=True)
#         self._renderThread.start()

#     def query(self, url):
#         self._requests.put(url)
#         resultUrl, htmlData = self._results.get()
#         assert url == resultUrl
#         return htmlData

# def renderThread(requests, results):
#     application = QtWidgets.QApplication(sys.argv)
#     render = MyMagicRender(requests, results)
#     application.exec_()

# # TODO Rename, render is shitty
# class Render(QtWebKitWidgets.QWebPage):
#     def __init__(self, requestsQueue, resultsQueue):
#         super().__init__()
#         self._requests = requestsQueue
#         self._results = resultsQueue
#         self._loadingUrl = None
#         self._timer = QtCore.QTimer()
#         self._timer.timeout.connect(self._work)
#         self.mainFrame().loadFinished.connect(self._onLoad)
#         self._timer.start(100)

#     def _work(self):
#         if self._loadingUrl is None:
#             url = None
#             try:
#                 url = self._requests.get_nowait()
#             except queue.Empty:
#                 pass
#             if url is not None:
#                 self._loadingUrl = url
#                 self.mainFrame().load(QtCore.QUrl(self._loadingUrl))

#     def _onLoad(self):
#         self._results.put((self._loadingUrl, self.mainFrame().toHtml()))
#         self._loadingUrl = None


# class MyMagicRender(Render):
#     def _onLoad(self):
#         print('FILL NOW')
#         dom = self.mainFrame().documentElement()
#         fld = dom.findFirst('input[id=card_search]')
#         fld.evaluateJavaScript('this.value = "Abbot"')
#         btn = dom.findFirst('button[class=search-button]')
#         print(btn)
#         print(btn.evaluateJavaScript('this.click()'))

# b = WebBrowser('foo')
# h = b.query('http://shop.mymagic.ru/card-search')
# # print(lxml.html.document_fromstring(h))

# # import core.logger


# # class Browser(object):
# #     def __init__(self, parentId):
# #         self.cookie = 1
# #         self.logger = core.logger.Logger('{}-browser'.format(parentId))
# #         self.exitEvent = threading.Event()
# #         self.htmlRequests = queue.Queue()
# #         self.htmlResults = queue.Queue()
# #         self.htmlObtainer = threading.Thread(name='{}-browser-thread'.format(parentId), target=setupBrowser, args=(self.htmlRequests, self.htmlResults, self.exitEvent, self.logger,), daemon=True)

# #     def query(self, url):
# #         self.cookie += 1
# #         newCookie = self.cookie
# #         self.htmlRequests.put((newCookie, url))
# #         # TODO

# # PRICE_HTML_DOWNLOAD_TIMEOUT_SECONDS = 45
# # PRICE_HTML_DOWNLOAD_CHECK_TIME_SECONDS = 5

# # class Browser(object):
# #     def __init__(self, parentId):
# #         self.cookie = 1
# #         self.logger = core.logger.Logger('{}-browser'.format(parentId))
# #         self.exitEvent = threading.Event()
# #         self.htmlRequests = queue.Queue()
# #         self.htmlResults = queue.Queue()
# #         self.htmlObtainer = threading.Thread(name='{}-browser-thread'.format(parentId), target=setupBrowser, args=(self.htmlRequests, self.htmlResults, self.exitEvent, self.logger,), daemon=True)

# #     def querySync(self, url):
# #         self.cookie += 1
# #         newCookie = self.cookie
# #         self.htmlRequests.put((newCookie, url))
# #         # TODO

# #     def queryAsync(self, url):
# #         pass


# # class Render(QtWebKitWidgets.QWebPage):
# #     def __init__(self, requests, results):
# #         super().__init__()
# #         self.mainFrame().loadFinished.connect(self.onLoadFinished)

# #     def request(self, url, cookie):


# #     def process(self, items):
# #         self._items = iter(items)
# #         self.fetchNext()

# #     def fetchNext(self):
# #         try:
# #             self._url, self._func = next(self._items)
# #             self.mainFrame().load(QtCore.QUrl(self._url))
# #         except StopIteration:
# #             return False
# #         return True

# #     def onLoadFinished(self):
# #         self.results.put((self.cookie, self.mainFrame().toHtml()))
# #         self.loading = False

# # def setupBrowser(requests, results, exitEvent, logger):
# #     application = QtWidgets.QApplication(sys.argv)
# #     browserStorage = { 'instance': QtWebKitWidgets.QWebView() }
# #     browserLock = threading.Lock()
# #     browserTimer = QtCore.QTimer()
# #     browserTimer.timeout.connect(functools.partial(waitHtmlData, browserStorage, browserLock, results, exitEvent, logger))
# #     browserTimer.start(100)
# #     workTimer = QtCore.QTimer()
# #     workTimer.timeout.connect(functools.partial(processRequests, workTimer, browserStorage, browserLock, requests, exitEvent, logger))
# #     workTimer.start(100)
# #     application.exec_()

# # def processRequests(timer, browserStorage, browserLock, requests, exitEvent, logger):
# #     if exitEvent.is_set():
# #         QtWidgets.QApplication.quit()
# #         # TODO stop timer?
# #         # TODO send signal to application object

# #     if not browserLock.acquire(blocking=False):
# #         return

# #     try:
# #         qualifiedUrl = requests.get_nowait()
# #     except queue.Empty:
# #         browserLock.release()
# #         return

# #     logger.info('Loading [GET] {}'.format(qualifiedUrl))
# #     browserStorage['start_time'] = time.time()
# #     browserStorage['instance'].load(QtCore.QUrl(qualifiedUrl))

# # def waitHtmlData(storage, browserLock, results, exitEvent, logger):
# #     if exitEvent.is_set():
# #         QtWidgets.QApplication.quit()
# #         # TODO stop timer?
# #         # TODO send signal to application object

# #     ct = time.time()
# #     browser = storage['instance']
# #     resultHtml = None
# #     htmlString = browser.page().mainFrame().toHtml()
# #     if 'priceGuideTable tablesorter' in htmlString: # TODO ZALEPA we need to create universal method
# #         sizeEquals = storage.get('last_size', -1) == len(htmlString)
# #         timePassed = ct - storage.get('last_time', ct) > PRICE_HTML_DOWNLOAD_CHECK_TIME_SECONDS
# #         if sizeEquals and timePassed:
# #             resultHtml = htmlString
# #         elif not sizeEquals:
# #             storage['last_size'] = len(htmlString)
# #             storage['last_time'] = ct

# #     if ct - storage.get('start_time', ct) > PRICE_HTML_DOWNLOAD_TIMEOUT_SECONDS:
# #         resultHtml = ''

# #     if resultHtml is not None:
# #         strUrl = browser.url().toString()
# #         results.put((strUrl, htmlString))
# #         logger.info('Finished [GET] {}'.format(strUrl))
# #         storage['instance'] = QtWebKitWidgets.QWebView()
# #         if 'start_time' in storage: del storage['start_time']
# #         if 'last_size' in storage: del storage['last_size']
# #         if 'last_time' in storage: del storage['last_time']
# #         browserLock.release()
