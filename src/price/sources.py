import json

import core.currency
import core.language
import core.logger


class TcgPlayer(object):
    def __init__(self, resultsQueue, storagePath, resources):
        self.priceResults = resultsQueue
        self.logger = core.logger.Logger('TcgPlayer')
        self.storagePath = storagePath
        with open(resources['sets']) as fobj:
            self.setAbbrvsToQueryStrings = json.load(fobj)
        self.setQueryStrings = set()
        for _, queryStrings in self.setAbbrvsToQueryStrings.items():
            self.setQueryStrings.update(queryStrings)

    def queryPrice(self, cardName, setAbbrv, language, foil, cookie):
        pass
        # self.priceRequests.put((cardName, setAbbrv, language, foil, cookie))

    def terminate(self):
        pass
