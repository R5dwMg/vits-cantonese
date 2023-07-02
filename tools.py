import opencc
import unicodedata
import re

s2t = opencc.OpenCC('s2t.json')
# hk2t = opencc.OpenCC('hk2t.json')
# t2tw = opencc.OpenCC('t2tw.json')
# s2hk = opencc.OpenCC('s2hk.json')
jp2t = opencc.OpenCC('jp2t.json')

punctuation = "\'\",.:；–—-－?!．，、。‧·…⋯《》「」（）()/:︰：;！？﹖ ﹔~～／”“⠀"

# ref http://olsgaard.dk/hiragana-katakana-transliteration-in-4-lines-of-python.html
katakana_chart = "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶヽヾ"
hiragana_chart = "ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖゝゞ"
hir2kat = str.maketrans(hiragana_chart, katakana_chart)
kat2hir = str.maketrans(katakana_chart, hiragana_chart)


def hira2kata(text: str) -> str:
    """
    Hiragana to katakana
    """
    return text.translate(hir2kat)


def kata2hira(text: str) -> str:
    """
    Katakana to hiragana
    """
    return text.translate(kat2hir)


def full2half(c: str) -> str:
    """
    Convert full character to half
    """
    return unicodedata.normalize("NFKC", c)


def has_latin(text) -> bool:
    """
    Check if text contains latin
    """
    latin_pattern = r'[a-zA-Z\.]+'
    return len(re.findall(latin_pattern, text, re.UNICODE)) > 0


def normalize_text(text: str) -> str:
    """
    Fix and convert text to
    - traditional chinese character
    - lowercase
    - latin in half
    """
    # convert latin to lowercase
    text = text.lower()
    # replace unknown symbol
    text = text.replace("￼", "")
    # convert full latin to half
    text = full2half(text)
    # convert simplified Chinese to traditional
    text = s2t.convert(text)
    # convert hk char to traditional
    text = jp2t.convert(text)

    return text


def load_text(path: str) -> str:
    with open(path, "r", encoding="utf8") as f:
        content = f.read()
    return content


def write_text(path: str, text: str):
    with open(path, "w", encoding="utf8") as f:
        f.write(text)
