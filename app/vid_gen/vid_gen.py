import os
import traceback

from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
from shortGPT.config.languages import EDGE_TTS_VOICENAME_MAPPING
from shortGPT.engine.short_video_engine import ShortVideoEngine
from shortGPT.gpt import gpt_chat_video

class VidGen:
    def __init__(self, art_style='normal', apply_background_music=False):
        self.isVertical = True
        self.voice_module = EdgeTTSVoiceModule('en-AU-WilliamNeural')
        self.language = 'English'
        self.script = ""
        self.video_folder = None
        self.video_id = ""
        self.art_style = art_style
        self.apply_background_music = apply_background_music

    def generate_script(self, message, video_duration: str = '30-60', script: str = None):
        self.script = script if script else gpt_chat_video.generateScript(message, video_duration=video_duration)
        return self.script

    def correct_script(self, correction):
        self.script = gpt_chat_video.correctScript(self.script, correction)
        return self.script

    def make_video(self, progress=None):
        videoEngine = ShortVideoEngine(voiceModule=self.voice_module, script=self.script, isVerticalFormat=self.isVertical, id=self.video_id, art_style=self.art_style, apply_background_music=self.apply_background_music)
        num_steps = videoEngine.get_total_steps()
        progress_counter = 0

        def logger(prog_str):
            if progress:
                progress(progress_counter / num_steps, f"Creating video - {progress_counter} - {prog_str}")

        videoEngine.set_logger(logger)
        for step_num, step_info in videoEngine.makeContent():
            if progress:
                progress(progress_counter / num_steps, f"Creating video - {step_info}")
            progress_counter += 1

        video_path = videoEngine.get_video_output_path()
        return video_path

# Example usage:
# vid_gen = VidGen()
# vid_gen.generate_script("Your video description here")
# vid_gen.make_video()