# Wizard of the Search 

![License: MIT](https://img.shields.io/github/license/refaim/wots.svg)
![Last Commit](https://img.shields.io/github/last-commit/refaim/wots.svg)
[![Travis CI](https://travis-ci.org/refaim/wots.svg?branch=master)](https://travis-ci.org/refaim/wots)
[![AppVeyor](https://ci.appveyor.com/api/projects/status/ifvfy7vy8kru9if8?svg=true)](https://ci.appveyor.com/project/refaim/wots)
[![Azure](https://dev.azure.com/rkharito/rkharito/_apis/build/status/azure.wots)](https://dev.azure.com/rkharito/rkharito/_build/latest?definitionId=1)
![Code Size](https://img.shields.io/github/languages/code-size/refaim/wots.svg)
[![Coverage Status](https://coveralls.io/repos/github/refaim/wots/badge.svg)](https://coveralls.io/github/refaim/wots)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/refaim/wots.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/refaim/wots/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/refaim/wots.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/refaim/wots/context:python)

Программа для поиска карт ККИ Magic the Gathering на русскоязычных торговых интернет-площадках.

Работает на Windows, Linux и OS X.

## Список поддерживаемых ресурсов
- [amberson.mtg.ru](http://amberson.mtg.ru/)
- [angrybottlegnome.ru](http://angrybottlegnome.ru/)
- [autumnsmagic.com](https://autumnsmagic.com/)
- [bigmagic.ru](http://bigmagic.ru/)
- [buymagic.com.ua](http://www.buymagic.com.ua/)
- [cardplace.ru](https://www.cardplace.ru/)
- [easyboosters.com](https://easyboosters.com/)
- [goodork.ru](https://goodork.ru/)
- [hexproof.ru](https://hexproof.ru/)
- [magiccardmarket.ru](http://magiccardmarket.ru/)
- [manapoint.mtg.ru](http://manapoint.mtg.ru/)
- [mtg.ru](http://www.mtg.ru/exchange/)
- [mtgsale.ru](https://mtgsale.ru/)
- [mtgshop.ru](http://mtgshop.ru/)
- [mtgtrade.net](http://mtgtrade.net/)
- [myupkeep.ru](http://myupkeep.ru/)
- [shop.mymagic.ru](https://shop.mymagic.ru/)
- [topdeck.ru](https://topdeck.ru/apps/toptrade/singles/search)

## Пример интерфейса программы
![Пример интерфейса](screenshot01.png)

## Сборка проекта из исходного кода
### Linux и Mac OS X
Требования: Python 3.6.
```
pip install -r requirements.txt
pip install -r requirements.test.txt
make test
make build
```
### Windows
Требования: Python 3.6, Microsoft Visual Studio 14.0
```
setup_windows.cmd
```
