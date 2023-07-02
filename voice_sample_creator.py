import os.path
import shutil

import pandas as pd
import pyttsx3

import audio_utils
import common_voice.utils
import zh_hk_to_ipa
from yue import picker as win_picker
from yue.utils import split_string, merge_sentences
from tools import load_text, write_text
import tools
import win_narrator_verifier
import synthesiser
from tqdm import tqdm

engine = pyttsx3.init()

post_process_exclude_field = [
    {"clip_src": "common_voice_zh-HK_23001122.mp3"}
]


def get_empty_dataset() -> pd.DataFrame:
    # id:int
    # ckpt:int
    # clip_src:str
    # clip_trans:str
    # sentence:str
    # genre:str (train, val)
    # synthesizer:str
    t = {
        "id": [],
        "ckpt": [],
        "clip_src": [],
        "clip_change": [],
        "transcript": [],
        "genre": [],
        "synthesizer": []
    }
    return pd.DataFrame(t)


def split_list(lst: [], size):
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def append_win_narrator_transcript(df_train: pd.DataFrame, df_val: pd.DataFrame, ckpt: int):
    """
    Generate transcript for win narrator
    """

    win_picker.pick("yue/data/cuhk_char_rank.csv", "win_narrator_unsupported.txt", "yue/data/yue.build.txt")
    win_supported_unique_phonetic = win_picker.data_win_supported_unique_phonetic
    win_lang_mix = win_picker.data_phrase_lang_mix

    # segment
    segment_phonetic = split_string("".join(win_supported_unique_phonetic), 15)
    merged_list = merge_sentences(win_lang_mix, 5)
    segment_lang_mix = [" ".join(l) for l in merged_list]
    segment_phonetic.extend(segment_lang_mix)
    data_list: list = segment_phonetic

    for t in data_list:
        row = {
            "id": None,
            "ckpt": ckpt,
            "clip_src": f"w-{ckpt}-{len(df_train)}.wav",
            "clip_change": "",
            "transcript": t,
            "genre": "train",
            "synthesizer": "win"
        }
        df_train.loc[len(df_train)] = row

    # add supplement
    # train, val
    content = load_text("dataset_raw/supplement/win_narrator/transcript.train.txt")
    train_data_list = content.split("\n")

    content = load_text("dataset_raw/supplement/win_narrator/transcript.val.txt")
    val_data_list = content.split("\n")

    for line in train_data_list:
        data = line.split("|")
        row = {
            "id": None,
            "ckpt": ckpt,
            "clip_src": f"{data[0]}",
            "clip_change": "",
            "transcript": f"{data[1]}",
            "genre": "train",
            "synthesizer": "win"
        }
        df_train.loc[len(df_train)] = row

    for line in val_data_list:
        data = line.split("|")
        row = {
            "id": None,
            "ckpt": ckpt,
            "clip_src": f"{data[0]}",
            "clip_change": "",
            "transcript": f"{data[1]}",
            "genre": "val",
            "synthesizer": "win"
        }
        df_val.loc[len(df_val)] = row

    pass


def append_voicevox_supplement(df_train: pd.DataFrame, df_val: pd.DataFrame, ckpt: int):
    content = load_text("dataset_raw/supplement/voicevox/transcript.train.txt")
    train_data_list = content.split("\n")

    content = load_text("dataset_raw/supplement/voicevox/transcript.val.txt")
    val_data_list = content.split("\n")

    for line in train_data_list:
        data = line.split("|")
        row = {
            "id": None,
            "ckpt": ckpt,
            "clip_src": f"{data[0]}",
            "clip_change": "",
            "transcript": f"{data[1]}",
            "genre": "train",
            "synthesizer": "voicevox"
        }
        df_train.loc[len(df_train)] = row

    for line in val_data_list:
        data = line.split("|")
        row = {
            "id": None,
            "ckpt": ckpt,
            "clip_src": f"{data[0]}",
            "clip_change": "",
            "transcript": f"{data[1]}",
            "genre": "val",
            "synthesizer": "voicevox"
        }
        df_val.loc[len(df_val)] = row


def gen_win_narrator_sample(path_dataset: str, output_folder: str):
    df = pd.read_table(path_dataset)
    df = df[df["synthesizer"] == "win"]

    win_narrator = synthesiser.WinNarrator()

    for row in df.iterrows():
        transcript = row[1]["transcript"]
        fname = row[1]["clip_src"]
        output_path = f"{output_folder}/{fname}"
        win_narrator.to_file(transcript, output_path)
        d = win_narrator_verifier.get_wav_duration(output_path)
        if d == 0:
            print(output_path, "is empty, speech: ", transcript)
    pass


def init_narrator():
    global engine
    engine.setProperty('volume', 1.0)

    voices = engine.getProperty('voices')  # getting details of current voice
    voice_id = voices[3].id
    engine.setProperty(
        'voice',
        # voices[self.speech_engine_index].id
        voice_id
    )  # zh-hk voice, changing index, changes voices. 1 for female


def append_common_voice_transcript(df_train: pd.DataFrame, df_val: pd.DataFrame, ckpt: int):
    """
    unsupported_char = win_unsupported
    supported_char = cuhk - unsupported_char
    use win narrator to generated supported char + chinese-english mixed phrase
    """
    # load yue set
    # zh_hk_to_ipa.init("yue/data/yue.build.txt")

    # extract chinese / english mix phrases
    # phrase_dict = zh_hk_to_ipa.phrase_dict
    # mix_phrase = []
    # for k, v in phrase_dict.items():
    #     if tools.has_latin(k):
    #         mix_phrase.append(k)

    # win narrator unsupported character set
    # win_narrator_unsupported = set()
    # with open("win_narrator_unsupported.txt", "r", encoding="utf8") as f:
    #     content = f.read()
    #     t = [c for c in content]
    #     win_narrator_unsupported.update(t)

    # load common voice train data
    df = common_voice.utils.load_dataset("common_voice/"
                                         "cv-corpus-8.0-2022-01-19-zh-HK.tar/"
                                         "cv-corpus-8.0-2022-01-19-zh-HK/"
                                         "cv-corpus-8.0-2022-01-19/zh-HK/preprocessed.tsv")
    df["vote"] = df["up_votes"] - df['down_votes']
    df = df[df["gender"] == "female"]
    df = df[df['sentence'].str.len() > 20]
    df = df[df["vote"] > 1]
    df = df.drop(["gender", "vote", "up_votes", "down_votes", "client_id", "age", "accents", "locale", "segment"],
                 axis=1)
    df["synthesizer"] = "common_voice"

    # generate training rows
    df_train_select = df.iloc[0:1000]
    for row in df_train_select.iterrows():
        entry = {
            "id": None,
            "ckpt": ckpt,
            "clip_src": f"{row[1]['path']}",
            "clip_change": "",
            "transcript": f"{row[1]['sentence']}",
            "genre": "train",
            "synthesizer": "common_voice"
        }
        df_train.loc[len(df_train)] = entry

    # generate validation rows
    df_val_select = df.iloc[1001:1201]
    for row in df_val_select.iterrows():
        entry = {
            "id": None,
            "ckpt": ckpt,
            "clip_src": f"{row[1]['path']}",
            "clip_change": "",
            "transcript": f"{row[1]['sentence']}",
            "genre": "val",
            "synthesizer": "common_voice"
        }
        df_val.loc[len(df_val)] = entry


def create_dataset():
    ckpt = 0
    df_train = get_empty_dataset()
    df_val = get_empty_dataset()
    append_win_narrator_transcript(df_train, df_val, ckpt)
    append_common_voice_transcript(df_train, df_val, ckpt)
    append_voicevox_supplement(df_train, df_val, ckpt)

    # update ids
    df_train["id"] = df_train.index
    df_val["id"] = df_val.index

    output_folder = f"dataset/ckpt_{ckpt}"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # save master file
    path_train = f"{output_folder}/dataset_train.tsv"
    path_val = f"{output_folder}/dataset_val.tsv"

    if os.path.exists(path_train):
        print(path_train, "is already there, clip_change will be lost if you overwrite")
    else:
        df_train.to_csv(path_train, sep="\t", index=False)

    if os.path.exists(path_val):
        print(path_val, "is already there, clip_change will be lost if you overwrite")
    else:
        df_val.to_csv(path_val, sep="\t", index=False)

def fix_dataset_id(path_train: str, path_val: str):
    df_train = pd.read_table(path_train)
    df_val = pd.read_table(path_val)
    df_train["id"] = df_train.index
    df_val["id"] = df_val.index
    df_train.to_csv(path_train, sep="\t", index=False)
    df_val.to_csv(path_val, sep="\t", index=False)
    pass

def resample_voice_clip(path_train: str, path_val: str):
    df_train = pd.read_table(path_train)
    df_val = pd.read_table(path_val)

    # select common_voice and win narrator
    # df_train = df_train[(df_train["synthesizer"] == "common_voice") | (df_train["synthesizer"] == "win")]
    # df_val = df_val[(df_val["synthesizer"] == "common_voice") | (df_val["synthesizer"] == "win")]

    input_change_folder = "dataset_raw/change/"
    input_voicevox_folder = "dataset_raw/supplement/voicevox"
    output_folder = "dataset_raw/resample"

    progress = tqdm(total=len(df_train) + len(df_val))

    # select common voice clips
    # train
    for index, row in df_train.iterrows():
        in_root = input_voicevox_folder if row['synthesizer'] == "voicevox" else input_change_folder
        audio_utils.preprocess(f"{in_root}/train/{row['clip_change']}",
                               f"{output_folder}/train/{row['clip_change']}", row["synthesizer"] == "common_voice")
        progress.update(1)

    # val
    for index, row in df_val.iterrows():
        in_root = input_voicevox_folder if row['synthesizer'] == "voicevox" else input_change_folder
        audio_utils.preprocess(f"{in_root}/val/{row['clip_change']}",
                               f"{output_folder}/val/{row['clip_change']}", row["synthesizer"] == "common_voice")
        progress.update(1)

    progress.close()


def compile_vits(path_train: str, path_val: str, ckpt: int):
    """
    Generate filelist.txt for train and val set
    Grab sound clip files to ckpt folder
    """
    df_train = pd.read_table(path_train)
    df_val = pd.read_table(path_val)
    dataset_root = f"/content/vits-cantonese/dataset/ckpt_{ckpt}"
    clip_src_root = "dataset_raw/resample"
    clip_src_voicevox_root = "dataset_raw/supplement/voicevox"
    clip_dest_root = f"dataset/ckpt_{ckpt}"

    def iter(df: pd.DataFrame, set_type: str):
        progress = tqdm(total=len(df))
        output = ""
        for index, row in df.iterrows():
            transcript = row['transcript']
            syn = row['synthesizer']
            clip_fname = row['clip_change']

            # set clip path
            clip_dataset_name = f"dataset_{row['id']}.wav"
            clip_path = f"{dataset_root}/{set_type}/{clip_dataset_name}"
            output += f"{clip_path}|{transcript}\n"

            # copy clip file and rename
            # if syn == "common_voice" or syn == "win":
            #     shutil.copyfile(f"{clip_src_root}/{set_type}/{clip_fname}", f"{clip_dest_root}/{set_type}/{clip_dataset_name}")
            # elif syn == "voicevox":
            #     shutil.copyfile(f"{clip_src_voicevox_root}/{set_type}/{clip_fname}", f"{clip_dest_root}/{set_type}/{clip_dataset_name}")
            shutil.copyfile(f"{clip_src_root}/{set_type}/{clip_fname}", f"{clip_dest_root}/{set_type}/{clip_dataset_name}")
            progress.update(1)

        progress.close()
        output = output.replace("\n\n", "")
        with open(f"dataset/ckpt_{ckpt}/zh_hk_{set_type}_filelist.txt", "w", encoding="utf8") as f:
            f.write(output)

    iter(df_train, "train")
    iter(df_val, "val")

    # output = ""
    # set_type = "val"
    # for index, row in df_val.iterrows():
    #     transcript = row['transcript']
    #     clip_path = f"{dataset_root}/{set_type}/dataset_{row['id']}.wav"
    #     output += f"{clip_path}|{transcript}\n"
    #
    # output = output.replace("\n\n", "")
    # with open(f"dataset/ckpt_{ckpt}/zh_hk_{set_type}_filelist.txt", "w", encoding="utf8") as f:
    #     f.write(output)


if __name__ == "__main__":
    ckpt = 0
    # create_dataset()

    # gen win narrator clips
    input_folder = f"dataset/ckpt_{ckpt}"
    path_dataset_train = f"{input_folder}/dataset_train.tsv"
    path_dataset_val = f"{input_folder}/dataset_val.tsv"

    # output_folder_train = f"dataset_raw/essential/win_narrator/train"
    # output_folder_val = f"dataset_raw/essential/win_narrator/val"
    #
    # gen_win_narrator_sample(path_dataset_train, output_folder_train)
    # gen_win_narrator_sample(path_dataset_val, output_folder_val)

    # resample audio
    # resample_voice_clip(path_dataset_train, path_dataset_val)
    #
    # fix_dataset_id(path_dataset_train, path_dataset_val)
    compile_vits(path_dataset_train, path_dataset_val, ckpt)

    pass
