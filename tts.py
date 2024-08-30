import os
import sys
import torch
from OpenVoice.openvoice.api import ToneColorConverter
from OpenVoice.MeloTTS.melo.api import TTS

#/* cSpell:disable */

sys.stdout.reconfigure(encoding='utf-8')

# Setup paths and device
ckpt_converter = 'OpenVoice/checkpoints2/converter'
device = "cuda:0" if torch.cuda.is_available() else "cpu"
output_dir = 'outputs_v2'
os.makedirs(output_dir, exist_ok=True)
print(f'Using device: {device}')

# Load models and embeddings
tone_color_converter = None
model = None
speaker_ids = None
source_se = None
target_se = None

def load_models():
    global tone_color_converter, model, speaker_ids, source_se, target_se
    try:
        # Load ToneColorConverter
        tone_color_converter = ToneColorConverter(f'{ckpt_converter}/config.json', device=device)
        tone_color_converter.load_ckpt(f'{ckpt_converter}/checkpoint.pth')

        # Load the saved target speaker embedding
        target_se = torch.load('OpenVoice/resources/target_se.pth', map_location=device)

        # Load the pre-trained TTS model
        model = TTS(language='EN', device=device)
        speaker_ids = model.hps.data.spk2id

        # Load the source speaker embedding
        source_se = torch.load('D:\\repos\\mine\\JarvisAssist\\OpenVoice\\checkpoints2\\base_speakers\\ses\\en-br.pth', map_location=device)

        print('Models and embeddings loaded successfully.')
    except Exception as e:
        print(f'An error occurred while loading models: {e}')
        sys.exit(1)

def synthesize_speech(text, output_path, speed=1.0):
    try:
        # Temporary path for the synthesized speech
        src_path = f'{output_dir}/tmp.wav'

        # Generate speech from text
        model.tts_to_file(text, speaker_ids['EN-BR'], src_path, speed=speed)

        # Run the tone color converter
        encode_message = "@MyShell"
        tone_color_converter.convert(
            audio_src_path=src_path, 
            src_se=source_se, 
            tgt_se=target_se, 
            output_path=output_path,
            message=encode_message
        )
        return output_path
        print(f'Speech synthesis complete. Output saved to {output_path}')
    except Exception as e:
        print(f'An error occurred during speech synthesis: {e}')

