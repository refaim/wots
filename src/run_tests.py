import os
import subprocess

import psutil

import card.sources


def main():
    logsPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'testlogs'))
    processes = []
    for classObject in card.sources.getCardSourceClasses():
        source = classObject()
        sourceId = source.getTitle()
        print(sourceId)
        processes.append(subprocess.Popen([
            'python3',
            'test_source.py',
            sourceId,
            os.path.join(logsPath, 'out_{}.log'.format(sourceId)),
            os.path.join(logsPath, 'err_{}.log'.format(sourceId)),
        ], shell=True))
    for p in processes:
        p.wait()
    return 0

if __name__ == '__main__':
    # noinspection PyBroadException
    try:
        main()
    except Exception:
        process = psutil.Process(os.getpid())
        for child in process.children(recursive=True):
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
