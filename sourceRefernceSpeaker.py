import os
import torch
from OpenVoice.openvoice import se_extractor
from OpenVoice.openvoice.api import ToneColorConverter

# Setup paths and device
ckpt_converter = 'OpenVoice/checkpoints2/converter'
device = "cuda:0" if torch.cuda.is_available() else "cpu"

# Load ToneColorConverter
tone_color_converter = ToneColorConverter(f'{ckpt_converter}/config.json', device=device)
tone_color_converter.load_ckpt(f'{ckpt_converter}/checkpoint.pth')

# Extract target speaker embedding
reference_speaker = 'OpenVoice/resources/Jarvis2.mp3'  # The voice you want to clone
target_se, audio_name = se_extractor.get_se(reference_speaker, tone_color_converter, vad=False)

# Save the extracted speaker embedding
torch.save(target_se, 'OpenVoice/resources/target_se.pth')
print("Target speaker embedding saved.")
