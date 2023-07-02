"""
mozilla common voice dataset utils
"""
import os
import pandas
import pandas as pd
import sys
import tools
from tqdm import tqdm

sys.path.append('../')
from trie import Trie

target_ipa_set = set()
target_char_set = set()
dataset_unique_char = set()
trie = Trie()


def load_target_ipa_set(path: str):
    with open(path, "r", encoding="utf8") as f:
        content = f.read()
    target_ipa_set.update(content.split(" "))
    target_ipa_set.remove("")

    # build trie
    for key in target_ipa_set:
        trie.insert(key)

    print("target set size", len(target_ipa_set))


def load_target_char_set(path: str):
    with open(path, "r", encoding="utf8") as f:
        content = f.read()
    content.replace("\n", "")
    content.replace("/", "")
    content.replace("[", "")
    content.replace("]", "")
    for char in content:
        target_char_set.add(char)
    print("target set size", len(target_char_set))


def eval_coverage(df: pandas.DataFrame):
    global dataset_unique_char

    for index, row in df.iterrows():
        text = row["sentence"]
        chunk = ""
        for c in text:
            dataset_unique_char.update(c)
            if c in target_ipa_set:
                target_ipa_set.remove(c)
            if c in target_char_set:
                target_char_set.remove(c)

            if trie.char_search(c):
                chunk += c
            else:
                # end of phrase
                if len(chunk):
                    if c in target_ipa_set:
                        target_ipa_set.remove(chunk)
                    chunk = ""
                    trie.reset_search()
                else:
                    if c in target_ipa_set:
                        target_ipa_set.remove(c)

                # process the breaker character
                if trie.char_search(c):
                    chunk += c
                else:
                    if c in target_ipa_set:
                        target_ipa_set.remove(c)
        if len(chunk):
            if chunk in target_ipa_set:
                target_ipa_set.remove(chunk)

    print("dataset unique char size", len(dataset_unique_char))
    print("updated target set size", len(target_ipa_set))
    print("updated unique char size", len(target_char_set))


def load_dataset(path):
    return pd.read_table(path, converters={'accents': str})


def preprocess(path: str) -> pd.DataFrame:
    """
    Clean up / fix dataset from common voice
    """
    df = load_dataset(path)
    sentences = df["sentence"]

    # eliminate simplified chinese characters
    progress = tqdm(total=len(sentences))
    for index in sentences.index:
        # Update the value
        sentence = sentences.at[index]
        sentence = tools.normalize_text(sentence)
        sentences.at[index] = sentence
        progress.update()

    df["sentence"] = sentences

    # Get the parent folder
    parent_folder = os.path.dirname(path)
    fpath = f"{parent_folder}/preprocessed.tsv"

    df.to_csv(fpath, sep="\t", index=False)

    return df


if __name__ == "__main__":
    dataset_list = [
        "zh-HK.tar/zh-HK/validated.tsv",
        "cv-corpus-8.0-2022-01-19-zh-HK.tar/cv-corpus-8.0-2022-01-19-zh-HK/cv-corpus-8.0-2022-01-19/zh-HK/validated_word_fixed.tsv"
    ]
    # df = load_dataset(dataset_list[1])
    # df = df[df["gender"] == "female"]
    # df = df[df['sentence'].str.len() > 10]
    # print("df size:", len(df))

    # load target set
    # load_target_ipa_set("../yue_unique_set.txt")
    # load_target_char_set("../yue.txt")
    # eval_coverage(df)

    df = preprocess(dataset_list[1])

    pass
