import re
from tools import load_text, write_text
from yue.utils import parse_text


def build(path_main: str, path_variant: str, path_additional: str, path_output: str):
    """
    Combine main, variant and additional, generate a new yue database
    """
    main_text = load_text(path_main)
    main_text = main_text.lower().replace("\n\n", "\n")

    add_text = load_text(path_additional)
    add_text = add_text.lower().replace("\n\n", "\n")

    output = main_text + "\n" + "\n" + add_text

    word_dict, phrase_dict = parse_text(output)

    variant_text = load_text(path_variant)
    variant_dict = parse_variant(variant_text)
    variant_text = variant_to_text(variant_dict, word_dict)

    variant_text = variant_text.lower().replace("\n\n", "\n")

    output = output + "\n" + variant_text

    write_text(path_output, output)

    pass


def variant_to_text(variant_dict: dict, word_dict: dict) -> str:
    """
    Convert variant to text data, following yue.txt format
    """
    output = ""
    for k, v in variant_dict.items():
        if k not in word_dict:
            if v in word_dict:
                ipa_tag = ", ".join([f"/{i}/" for i in word_dict[v]])
                output += f"{k}\t{ipa_tag}\n"
            else:
                print(v, "is unknown")
    return output


def parse_variant(text: str) -> {}:
    """
    Parse variant to dict
    """
    output = {}
    lines = text.split("\n")
    for line in lines:
        data = line.split("	")
        origin_char = data[0]
        variant_list = data[1].split(" ")
        for v_char in variant_list:
            output[v_char] = origin_char
    return output


def broken_char_fix(path_main: str, path_fix_table: str, path_output: str):
    """
    Fix broken character
    convert 扌＋咼 to 𢰸 according to fix_table
    save fixed yue main table as output path
    """
    r = r'\[([^[\]]+)\]'

    # read original file
    content = load_text(path_main)
    content_list = content.split("\n")

    # read fix dict
    content = load_text(path_fix_table)
    fix_list = content.split("\n")

    fix_dict = {}
    for line in fix_list:
        d = line.split("|")
        fix_dict[d[0]] = d[1]

    output = []

    for line in content_list:
        matches = re.findall(r, line)
        skip_line = False
        if len(matches):
            for m in matches:
                if m in fix_dict:
                    fix = fix_dict[m]
                    if fix == "X":
                        skip_line = True
                        break
                    else:
                        line = line.replace(f"[{m}]", fix)
                else:
                    print(m, "not found")
        if not skip_line:
            output.append(line)

    output_text = "\n".join(output)
    with open(path_output, "w", encoding="utf8") as f:
        f.write(output_text)

    print("length check", len(content_list), len(output))
    pass


def broken_char_search():
    """
    Analysze and fix issues of yue.txt
    Look for broken character, export report yue_borken_char.txt
    """
    with open("yue/data/yue.txt", "r", encoding="utf8") as f:
        content = f.read()

    # search fo broken apart characters
    matches = re.findall(r'\[([^[\]]+)\]', content)
    output_set = set()
    output_set.update(matches)
    output = "\n".join(list(output_set))

    with open("yue/data/yue_broken_char_report.txt", "w", encoding="utf8") as f:
        f.write(output)

    pass


if __name__ == "__main__":
    build("data/yue_broken_char_fixed.txt", "data/variant.txt", "data/yue_additional.txt", "data/yue.build.txt")
    pass
