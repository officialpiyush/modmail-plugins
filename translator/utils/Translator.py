from googletrans import Translator as CoreTranslator

class Translator:
    def __init__(self):
        self.t = CoreTranslator()
    
    def translate(self, msg: str, dest: str = "en"):
        return CoreTranslator.translate(msg,dest=dest)