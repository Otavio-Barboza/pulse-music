# import geral
from deep_translator import MyMemoryTranslator


class Translator(MyMemoryTranslator):
    def __init__(
        self, 
        source = "auto", 
        target = "en-US", 
        proxies = None, 
        **kwargs
    ):
        super().__init__(source, target, proxies, **kwargs)