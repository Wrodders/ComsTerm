import serial, serial.tools.list_ports, platform

from core.device import TopicMap
from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QColor
import sys, platform, glob, enum
from typing import List



def scanUSB() -> list:
    ports = [p.device for p in serial.tools.list_ports.comports()]
    return ports


class Trie:
    def __init__(self):
        self.children = {}
        self.is_word_end = False

    def insert(self, word):
        for char in word:
            self = self.children.setdefault(char, Trie())
        self.is_word_end = True

    def words_with(self, prefix):
        if self.is_word_end:
            yield prefix
        for char, node in self.children.items():
            yield from node.words_with(prefix + char)

    def autocomplete(self, prefix) -> list():
        try:
            for char in prefix:
                self = self.children[char]
            return list(self.words_with(prefix))
        except KeyError:
            return []
        


def scanTopics() -> TopicMap:
    topicPubMap = TopicMap()
    topicPubMap.register(topicName="LINE", topicArgs=["L", "C","R" ], delim=":")
    topicPubMap.register(topicName="ACCEL", topicArgs=["X", "Y","Z" ], delim=":")
    return topicPubMap



