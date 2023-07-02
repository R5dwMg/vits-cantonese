import pandas as pd
from yue.utils import parse_text
import sys
from tools import load_text, write_text

sys.path.append("../")
from tools import has_latin

data_unknown_char: set = set()
data_unique_phonetic: set = set()
data_win_supported_unique_phonetic: set = set()
data_phrase_lang_mix: set = set()


def analyze_char_set(path_yue: str, ranked_char_list: list, char_set_name: str):
    """
    Analyze a given character set with yue database
    1. what are the characters in char_set not supported by yue database
    2. what are the characters having unique phonetic
    Text report will be generated
    """
    text_yue = load_text(path_yue)
    word_dict, phrase_dict = parse_text(text_yue)

    unknown_char_set = set()
    for c in ranked_char_list:
        if c not in word_dict:
            unknown_char_set.add(c)

    output = "\n".join(list(unknown_char_set))
    # write_text(f"data/{char_set_name}_unsupported_by_yue.txt", output)

    phonetic_set = set()
    char_unique_set = set()
    # find unique phonetic in char_set
    for c in ranked_char_list:
        if c in word_dict:
            phonetic = word_dict[c][0]
            if phonetic not in phonetic_set:
                phonetic_set.add(phonetic)
                char_unique_set.add(c)

    output = "\n".join(list(char_unique_set))
    # write_text(f"data/{char_set_name}_unique_phonetic.txt", output)

    return unknown_char_set, char_unique_set, word_dict, phrase_dict


def char_verifier(path_yue: str, character: []):
    """
    verify ipa symbols in yue file are supported by character list in config json
    """
    data_set = set()
    text_yue = load_text(path_yue)
    word_dict, phrase_dict = parse_text(text_yue)
    for key, ipa_list in word_dict.items():
        for ipa in ipa_list:
            ipa = ipa.replace("/", "")
            clist = [*ipa]
            for c in clist:
                data_set.add(c)

    for key, ipa_list in phrase_dict.items():
        for ipa in ipa_list:
            ipa = ipa.replace("/", "")
            clist = [*ipa]
            for c in clist:
                data_set.add(c)

    unmatch = set()
    c_set = set(character)
    for c in data_set:
        if c not in c_set:
            unmatch.add(c)

    if len(unmatch):
        print("".join(unmatch))
    else:
        print("perfect !")

    pass


def pick(path_ranked_char: str, path_win_unsupported: str, path_yue: str):
    global data_unknown_char
    global data_unique_phonetic
    global data_win_supported_unique_phonetic
    global data_phrase_lang_mix

    # load chuk as set, unsupported text
    df = pd.read_csv(path_ranked_char)

    # find out the unique characters, remove from cuhk char list, as essential list
    ranked_cuhk_list = list(df["char"])

    win_unsupported = load_text(path_win_unsupported)
    win_unsupported = {*win_unsupported}

    unknown_char_set, char_unique_set, word_dict, phrase_dict = analyze_char_set(path_yue, ranked_cuhk_list, "cuhk")
    print("unknown size", len(unknown_char_set))
    print("unique size", len(char_unique_set))

    known_unique_set = char_unique_set - unknown_char_set
    print("known unique size", len(known_unique_set))

    win_known_unique_set = known_unique_set - win_unsupported
    print("win known unique size", len(win_known_unique_set))

    unknown_char_set = win_unsupported.union(unknown_char_set)
    print("combined unsupported set", len(unknown_char_set))

    phrase_lang_mix = set()
    for k, v in phrase_dict.items():
        if has_latin(k):
            phrase_lang_mix.add(k)

    print("lang mix phrase size", len(phrase_lang_mix))

    data_unknown_char = unknown_char_set
    data_unique_phonetic = known_unique_set
    data_win_supported_unique_phonetic = win_known_unique_set
    data_phrase_lang_mix = phrase_lang_mix
    pass


if __name__ == "__main__":
    # pick("../cuhk_char_rank.csv", "../win_narrator_unsupported.txt", "data/yue.build.txt")
    char_verifier("data/yue.build.txt",
                  ["_", ",", ".", "!", "?", "~", "\u2026", "\u2500", "#", "N", "a", "b", "d", "e", "f", "g", "h", "i",
                   "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u", "v", "w", "x", "y", "z", "\u00e6", "\u00e7",
                   "\u00f8", "\u014b", "\u0153", "\u0235", "\u0250", "\u0251", "\u0252", "\u0253", "\u0254", "\u0255",
                   "\u0257", "\u0258", "\u0259", "\u025a", "\u025b", "\u025c", "\u0263", "\u0264", "\u0266", "\u026a",
                   "\u026d", "\u026f", "\u0275", "\u0277", "\u0278", "\u027b", "\u027e", "\u027f", "\u0282", "\u0285",
                   "\u028a", "\u028b", "\u028c", "\u028f", "\u0291", "\u0294", "\u02a6", "\u02ae", "\u02b0", "\u02b7",
                   "\u02c0", "\u02d0", "\u02e5", "\u02e6", "\u02e7", "\u02e8", "\u02e9", "\u0303", "\u031a", "\u0325",
                   "\u0329", "\u1d00", "\u1d07", "\u2191", "\u2193", "\u2205", "\u2c7c", " ",
                   "ɡ", "ɲ", "ʃ", "ʤ", "ᵊ", ":", "͡", "ʧ", "ɰ", "ˈ", "ʲ", "ɨ"])
    # l = [*"一二三四五六七八九十百千萬億兆"]
    # for i in range(9):
    #     se = generate_random_string(12, l, "")
    #     print(se)
