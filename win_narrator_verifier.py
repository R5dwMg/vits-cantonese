import os.path
import wave
import pyttsx3
import pandas as pd
from tqdm import tqdm

engine = pyttsx3.init()


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


def to_file(text, path):
    global engine
    engine.save_to_file(text, str(path))
    engine.runAndWait()


def verify_char_list():
    """
    Verify what windows narrator cannot read,
    record would be exported to win_narrator_unsupported.txt
    """
    # load data file
    df = pd.read_csv("yue/data/cuhk_char_rank.csv")

    output_folder = "win_narrator_voice_sample"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    unreadible = ""

    progress = tqdm(total=len(df))
    for index, row in df.iterrows():
        c = row['char']
        output_path = f"{output_folder}/{row['rank']}-{c}.wav"
        to_file(c, output_path)
        d = get_wav_duration(output_path)
        if d == 0:
            unreadible += c
        os.remove(output_path)
        progress.update(1)

    with open("win_narrator_unsupported.txt", "w", encoding="utf8") as f:
        f.write(unreadible)



def get_wav_duration(file_path):
    with wave.open(file_path, 'rb') as wav_file:
        num_frames = wav_file.getnframes()
        sample_rate = wav_file.getframerate()
        duration = num_frames / float(sample_rate)
        return duration


if __name__ == "__main__":
    init_narrator()

    # verify_char_list()

    to_file("nia", "win_narrator_voice_sample/nia.wav")

    # output_folder = "win_narrator_voice_sample"
    # if not os.path.exists(output_folder):
    #     os.makedirs(output_folder)
    #
    # # try read
    # text = "𨳒𨳊𨶙𨳍閪"
    # output_path = f"{output_folder}/{text}.wav"
    # to_file(text, output_path)
    # d = get_wav_duration(output_path)
    # print("length", d)
    #
    # text = "你"
    # output_path = f"{output_folder}/{text}.wav"
    # to_file(text, output_path)
    # d = get_wav_duration(output_path)
    # print("length", d)
