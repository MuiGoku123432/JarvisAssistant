import os
import sys
import torch
from OpenVoice.openvoice.api import ToneColorConverter
from OpenVoice.MeloTTS.melo.api import TTS

sys.stdout.reconfigure(encoding='utf-8')

# Setup paths and device
ckpt_converter = 'OpenVoice/checkpoints2/converter'
device = "cuda:0" if torch.cuda.is_available() else "cpu"
output_dir = 'outputs_v2'
os.makedirs(output_dir, exist_ok=True)

# Load ToneColorConverter
tone_color_converter = ToneColorConverter(f'{ckpt_converter}/config.json', device=device)
tone_color_converter.load_ckpt(f'{ckpt_converter}/checkpoint.pth')

# Load the saved target speaker embedding
target_se = torch.load('OpenVoice/resources/target_se.pth', map_location=device)

# Text to be synthesized
text = (
    """Of course, sir. The Jetson Nano project demonstrates impressive ingenuity and strategy. 
    The thermal camera on USB 0 and the IR camera on USB 1, paired with the Google Cardboard headset, create a sophisticated dual-viewing system. 
    Implementing GPIO for mode cycling is an excellent choice, providing intuitive and efficient control over the display modes. 
    Your integration of these technologies shows exceptional foresight in both user experience and technical execution. 
    Would you like me to initiate further enhancements to streamline the system's responsiveness and processing efficiency?"""
)

# Temporary path for the synthesized speech
src_path = f'{output_dir}/tmp.wav'

# Speed of the synthesized speech
speed = 1.0

# Load the pre-trained TTS model
model = TTS(language='EN', device=device)
speaker_ids = model.hps.data.spk2id

# Load the source speaker embedding
source_se = torch.load('D:\\repos\\mine\\JarvisAssist\\OpenVoice\\checkpoints2\\base_speakers\\ses\\en-br.pth', map_location=device)

# Generate speech from text
model.tts_to_file(text, speaker_ids['EN-BR'], src_path, speed=speed)

# Path to save the final output
save_path = f'{output_dir}/output_v2_EN-BR3.wav'

# Run the tone color converter
encode_message = "@MyShell"
tone_color_converter.convert(
    audio_src_path=src_path, 
    src_se=source_se, 
    tgt_se=target_se, 
    output_path=save_path,
    message=encode_message
)

print(f'Speech synthesis complete. Output saved to {save_path}')
