import matplotlib.pyplot as plt
import IPython.display as ipd

import os
import json
import math
import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader

import commons
import utils
from data_utils import TextAudioLoader, TextAudioCollate, TextAudioSpeakerLoader, TextAudioSpeakerCollate
from models import SynthesizerTrn
from text.symbols import symbols
from text import text_to_sequence

from scipy.io.wavfile import write
import opencc
import soundfile as sf
import zh_hk_to_ipa

path_model_root = "models/dataset_ckpt_0/"
path_model = f"{path_model_root}/G_20000.pth"
path_model_config = f"{path_model_root}/config.json"


def get_text(text, hps):
    text_norm = text_to_sequence(text, hps.data.text_cleaners)
    if hps.data.add_blank:
        text_norm = commons.intersperse(text_norm, 0)
    text_norm = torch.LongTensor(text_norm)
    return text_norm


def run():
    hps = utils.get_hparams_from_file(path_model_config)

    net_g = SynthesizerTrn(
        len(symbols),
        hps.data.filter_length // 2 + 1,
        hps.train.segment_size // hps.data.hop_length,
        **hps.model).cuda()
    _ = net_g.eval()

    _ = utils.load_checkpoint(path_model, net_g, None)

    # t2s = opencc.OpenCC('t2s.json')
    # input_text = t2s.convert("我愛你")
    # stn_tst = get_text("[GD]" + input_text + "[GD]", hps)

    # input_text = zh_hk_to_ipa.ipa("我愛你")
    stn_tst = get_text("食環署已聯同消防處和機電工程署開展檢討各公眾熟食場地的火警風險的工作", hps)

    with torch.no_grad():
        x_tst = stn_tst.cuda().unsqueeze(0)
        x_tst_lengths = torch.LongTensor([stn_tst.size(0)]).cuda()
        audio = net_g.infer(x_tst, x_tst_lengths, noise_scale=.667, noise_scale_w=0.8, length_scale=1.2)[0][
            0, 0].data.cpu().float().numpy()
    ipd.display(ipd.Audio(audio, rate=hps.data.sampling_rate, normalize=False))

    # save audio
    sf.write('audio.mp3', audio, 22050, format='mp3')


if __name__ == "__main__":
    run()
