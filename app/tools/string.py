import re

LETTERS_CLUSTER_RE = re.compile(r'(\w+)', re.U)


def splitByNonLetters(stringValue):
    result = []
    for match in LETTERS_CLUSTER_RE.finditer(stringValue):
        cluster = match.group(1)
        if cluster:
            result.extend(cluster.split(u'_'))
    return result


def parseSpacedInteger(stringValue):
    result = None
    if stringValue is not None:
        joined = ''.join(stringValue.split())
        if joined.isdigit():
            result = int(joined)
    return result
