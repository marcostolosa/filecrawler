import json
from pathlib import Path

from filecrawler.libs.file import File
from filecrawler.libs.parser import Parser
from filecrawler.util.color import Color
from filecrawler.util.logger import Logger
from filecrawler.parserbase import ParserBase


class DefaultParser(ParserBase):

    def __init__(self):
        super().__init__('Default', 'Parser for PDF files')

    def parse(self, file: File) -> dict:
        from filecrawler.config import Configuration
        data = {'content': self.get_readable_data(file)}

        if file.mime == 'application/json' and file.size < 1024 * 1024:
            try:
                data['object_content'] = json.loads(data['content'])
            except:
                pass

        return data
