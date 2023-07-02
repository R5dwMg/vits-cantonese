import random
import re


def parse_text(text: str) -> []:
    """
    Put data to dictionary
    """
    word_dict = {}
    phrase_dict = {}

    # clean up data
    data = re.sub(r'\[.*?\]', '', text)
    data = data.replace("/", "").replace("…", "").replace("，", "").replace("？", "").replace("！", "")
    data = data.lower()

    # split into lines
    data_lines = data.split("\n")
    idx = 1

    for line in data_lines:
        if len(line):
            line_data = line.split("\t")
            word = line_data[0]
            ipa_tag = line_data[1].split(", ")
            temp = []
            for t in ipa_tag:
                temp.extend(t.split(" "))
                ipa_tag = temp
            if len(word) == 1:
                word_dict[word] = ipa_tag
            else:
                phrase_dict[word] = ipa_tag
        idx += 1

    return word_dict, phrase_dict


def generate_random_string(length, characters, sep):
    random_string = sep.join(random.choice(characters) for _ in range(length))
    return random_string


def split_string(string: str, length: int) -> []:
    """
    Split a string by provided length, return sentences in list
    """
    return [string[i:i + length] for i in range(0, len(string), length)]


def merge_sentences(sentences: set, num_sentences_per_list: int):
    merged_lists = []
    current_list = []

    for sentence in sentences:
        current_list.append(sentence)

        if len(current_list) == num_sentences_per_list:
            merged_lists.append(current_list)
            current_list = []

    if current_list:
        merged_lists.append(current_list)

    return merged_lists