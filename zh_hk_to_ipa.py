# load data
import re
import opencc
import pandas as pd
import common_voice.utils
import tools
import cn2an
from yue import builder

word_dict = {}
phrase_dict = {}
phrase_tree = {}
char_to_phon = {}
phon_to_char = {}
phon_weight_tree = {}
punctuation = tools.punctuation
punctuation_normalize = {}

from trie import Trie

trie = Trie()


def init(data_path: str):
    global word_dict, phrase_dict, punctuation_normalize
    # load file
    with open(data_path, "r", encoding="utf8") as f:
        word_dict, phrase_dict = builder.parse_text(f.read())

    for key, word in phrase_dict.items():
        trie.insert(key)

    punctuation_normalize = {
        "，": ",",
        "、": ",",
        "。": ".",
        "？": "?",
        "﹖": "?",
        "！": "!",
        "～": "~",
        "…": " ",
        "⋯": " ",
        "．": "點",
        "‧": "點",
        "·": "點",
        " ": " "
    }

    # print("word dict", getsizeof(word_dict))
    # print("phrase dict", getsizeof(phrase_dict))


def parse_ipa(text: str) -> []:
    """
    Sentence to ipa, validation text, unknown char
    """
    phrase_found = []
    ipa_list = []
    text_val = ""
    chunk = ""
    unknown_char = []

    text = text.strip()

    for i in range(len(text)):
        c = text[i]
        if trie.char_search(c):
            chunk += c
        else:
            # c is not part of phrase or indicate end of phrase
            if len(chunk):
                # handle end of phrase, c triggered end of phrase
                if chunk in phrase_dict:
                    # chunk is found in phrase dictionary
                    # append to phrase dict and clean up
                    phrase_found.append(chunk)
                    ipa_list.append((chunk, phrase_dict[chunk],))
                    text_val += chunk
                    chunk = ""
                    trie.reset_search()
                else:
                    for cc in chunk:
                        # chunk is not in phrase dict
                        if cc in word_dict:
                            # chunk is in word dict
                            ipa_list.append((cc, word_dict[cc],))
                            text_val += cc
                        else:
                            unknown_char.append(cc)
                    chunk = ""
                    trie.reset_search()

                # handle character c
                # chat is c is part of another phrase
                if trie.char_search(c):
                    # c is part of phrase
                    chunk += c
                elif c in word_dict:
                    # c is not part of phrase
                    ipa_list.append((c, word_dict[c],))
                    text_val += c
                elif c in punctuation:
                    # c is punctuation
                    ipa_list.append((c, c,))
                    text_val += c
                else:
                    unknown_char.append(c)
            else:
                # single word and chunk currently empty
                if c in word_dict:
                    ipa_list.append((c, word_dict[c],))
                    text_val += c
                elif c in punctuation:
                    # c is punctuation
                    ipa_list.append((c, c,))
                    text_val += c
                else:
                    unknown_char.append(c)

    # iterated all characters
    # flush data in chunk
    remain_size = len(chunk)
    if remain_size == 1:
        # chunk is a character
        if chunk in word_dict:
            ipa_list.append((chunk, word_dict[chunk]))
            text_val += chunk
        elif chunk in word_dict:
            # chunk is not part of phrase
            ipa_list.append((chunk, word_dict[chunk],))
            text_val += chunk
        elif chunk in punctuation:
            # chunk is punctuation
            ipa_list.append((chunk, chunk,))
            text_val += chunk
        else:
            unknown_char.append(chunk)
    elif remain_size > 1:
        if chunk in phrase_dict:
            ipa_list.append((chunk, phrase_dict[chunk]))
            text_val += chunk
        else:
            for cc in chunk:
                if cc in word_dict:
                    # chunk is in word dict
                    ipa_list.append((cc, word_dict[cc],))
                    text_val += cc
                else:
                    unknown_char.append(cc)

    trie.reset_search()
    # export ipa list, text for validation, unknown characters
    return ipa_list, text_val, unknown_char


def flatten(ipa_list) -> str:
    """
    Merge ipa to string
    """
    items = [x[1][0] for x in ipa_list]
    ipa_text = ' '.join(items)
    ipa_text = ipa_text.replace("/", "")
    ipa_text = ipa_text.replace("  ", "")
    return ipa_text


def number_to_cantonese(text):
    return re.sub(r'\d+(?:\.?\d+)?', lambda x: cn2an.an2cn(x.group()), text)


s2t_converter = opencc.OpenCC('s2t')


def ipa(text: str):
    # convert numbers to number reading
    text = number_to_cantonese(text)

    # convert to lowercase
    text = text.lower()

    # normalize punctuations
    cl = [*text]
    for i in range(len(cl)):
        c = cl[i]
        if c in punctuation_normalize:
            cl[i] = punctuation_normalize[c]
        elif c in punctuation:
            cl[i] = ""
    text = "".join(cl)

    # convert simplified chinese to traditional
    text = s2t_converter.convert(text)

    # convert hiragana to katakana
    text = tools.hira2kata(text)

    ipa_list, text_val, unknown_char = parse_ipa(text)
    return flatten(ipa_list)


def merge(path_1, path_2, output_path: str):
    """
    Merge 2 yue database, export new one
    """
    with open(path_1, "r", encoding="utf8") as f:
        f1 = f.read()

    with open(path_2, "r", encoding="utf8") as f:
        f2 = f.read()
    f2 = f2.replace("   ", "\2")

    output = (f1 + "\n" + f2).replace("\n\n", "\n").lower()
    with open(output_path, "w", encoding="utf8") as f:
        f.write(output)
    pass


def test_in_out():
    text = "龜甲"
    ipa_list, val, unknown_char = parse_ipa(text)
    ipa_text = flatten(ipa_list)
    print(text)
    print(ipa_list)
    print(ipa_text)
    print("val:", text == val)
    print("unknown:", unknown_char)


def create_unique_ipa_dict():
    ipa_set = set()
    unique_dict = {}

    # process phrase
    for key, ipa_tags in phrase_dict.items():
        # ipa_tags = ipa_tags.replace("/", "")
        # tags = []
        # tags.extend(ipa_tags.split(" "))
        tags = ipa_tags
        for tag in tags:
            if tag not in ipa_set:
                unique_dict[key] = ipa_tags
        ipa_set.update(tags)

    # process characters
    for key, ipa_tag in word_dict.items():
        # ipa_tag = ipa_tag.replace("/", "")
        if ipa_tag not in ipa_set:
            unique_dict[key] = ipa_tag
        ipa_set.update(ipa_tag)

    output = ""
    for key, ipa_tag in unique_dict.items():
        line = f"{key}\t{ipa_tag}"
        output += line

    # write unique
    with open("yue/data/yue_unique.txt", "w", encoding="utf8") as f:
        f.write(output)

    output = ""
    output_set = ""
    idx = 0
    for key, ipa_tag in unique_dict.items():
        output += key + " "
        output_set += key + " "
        idx += 1
        if idx == 10:
            output += "\n"
            idx = 0

    with open("yue/data/yue_essential_script.txt", "w", encoding="utf8") as f:
        f.write(output)

    with open("yue/data/yue_unique_set.txt", "w", encoding="utf8") as f:
        f.write(output_set)

    print("size", len(ipa_set))

    pass


def verifier(sentences: pd.Series):
    import pandas as pd
    from tqdm import tqdm
    report = {
        "ipa": [],
        "val": [],
        "input": [],
        "val_output": [],
        "unknown": []
    }

    progress = tqdm(total=len(sentences))
    for s in sentences:
        ipa_list, text_val, unknown_char = parse_ipa(s)
        report["ipa"].append(str(ipa_list))
        report["val"].append(text_val == s)
        report["input"].append(s)
        report["val_output"].append(text_val)
        report["unknown"].append(unknown_char)
        progress.update(1)

    progress.close()

    df = pd.DataFrame(report)
    df = df[df["val"] == False]
    df.to_csv("ipa_verify.csv")

    error_rate = (len(df) / len(sentences)) * 100

    unknown_output = set()
    u = df["unknown"]
    for v in u:
        unknown_output.update(v)

    unknown_output = "\n".join(list(unknown_output))

    print("error rate", f"{error_rate}%")

    with open("ipa_verify_unknown.txt", "w", encoding="utf8") as f:
        f.write(unknown_output)


def verify_by_common_voice():
    df = common_voice.utils.load_dataset(
        "common_voice/cv-corpus-8.0-2022-01-19-zh-HK.tar/cv-corpus-8.0-2022-01-19-zh-HK/cv-corpus-8.0-2022-01-19/zh-HK/preprocessed.tsv")
    verifier(df["sentence"])


def test_ipa_process():
    converted = ipa("ABCD今天我们时间很足，太阳公公心情也很好。こんにちは1000.50")
    print(converted)


def run():
    init("yue/data/yue.build.txt")

    # test ipa() by one sentence
    # test_in_out()

    # test by ipa() by common voice database
    # verify_by_common_voice()

    test_ipa_process()

    # create_unique_ipa_dict()

    # check broken char in yue.txt
    # db_analyize()

    # merge additonal txt to new database
    # merge("yue_borken_char_fixed.txt", "yue_additional.txt", "yue.2.txt")

    pass


if __name__ == "__main__":
    run()
    # test_symbol()
