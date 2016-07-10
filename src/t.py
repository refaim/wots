# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys

# driver = webdriver.Ie()
# driver.get("http://www.python.org")
# assert "Python" in driver.title
# elem = driver.find_element_by_name("q")
# elem.send_keys("pycon")
# elem.send_keys(Keys.RETURN)
# assert "No results found." not in driver.page_source
# driver.close()

import sys

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtWebKitWidgets

app = QtWidgets.QApplication(sys.argv)

browser = QtWebKitWidgets.QWebView()
browser.load(QtCore.QUrl(sys.argv[1]))
browser.show()
# frame = browser.page().mainFrame()
# print(frame.title())

app.exec_()
