import datetime
import os
import subprocess
import re
import math
import shutil

from shortGPT.api_utils.pexels_api import getBestVideo
from shortGPT.audio import audio_utils
from shortGPT.audio.audio_duration import get_asset_duration
from shortGPT.audio.voice_module import VoiceModule
from shortGPT.config.asset_db import AssetDatabase, AssetType
from shortGPT.config.languages import Language
from shortGPT.editing_framework.image_to_videos import convert_images_to_videos
from shortGPT.api_utils.dalle_api import generate_simple_prompts, generate_image_urls
from shortGPT.editing_framework.editing_engine import (EditingEngine,
                                                       EditingStep)
from shortGPT.editing_utils import captions
from shortGPT.engine.abstract_content_engine import AbstractContentEngine
from shortGPT.gpt import gpt_editing, gpt_translate, gpt_yt
from shortGPT.gpt.gpt_bg_music_search_term import generate_search_term
from shortGPT.api_utils.pexels_api import search_audio_on_pexels
from shortGPT.api_utils.youtube_api import search_youtube_videos
from shortGPT.engine.short_video_engine import ShortVideoEngine
from app.logger import logger


class TestShortVideoEngine(ShortVideoEngine):

    def __init__(self, voiceModule: VoiceModule, script: str, background_music_name="", id="",
                 watermark=None, isVerticalFormat=False, language: Language = Language.ENGLISH, art_style='normal', apply_background_music=False):
        super().__init__(voiceModule=voiceModule, script=script, isVerticalFormat=isVerticalFormat, id=id, art_style=art_style, apply_background_music=apply_background_music)
        
        self._db_temp_audio_path = ".editing_assets/general_video_assets/6136eb114f5f40d8a671f455/temp_audio_path.wav"
        self._db_audio_path = ".editing_assets/general_video_assets/6136eb114f5f40d8a671f455/temp_audio_path.wav"
        self._db_timed_captions = [((0, 0.5199999809265137), 'Have you'), ((0.5199999809265137, 1.0), 'ever wondered'), ((1.0, 1.6799999475479126), 'how a single'), ((1.6799999475479126, 2.1600000858306885), 'image could'), ((2.1600000858306885, 2.619999885559082), 'change the'), ((2.619999885559082, 3.319999933242798), 'course of'), ((3.319999933242798, 4.559999942779541), 'history Let'), ((4.559999942779541, 5.079999923706055), 'me take you'), ((5.079999923706055, 5.659999847412109), 'back to the'), ((5.659999847412109, 6.159999847412109), 'Second World'), ((6.159999847412109, 6.71999979019165), 'War where'), ((6.71999979019165, 8.020000457763672), 'innovation and'), ((8.020000457763672, 8.020000457763672), 'deception'), ((8.020000457763672, 8.4399995803833), 'played a'), ((8.4399995803833, 9.020000457763672), 'crucial role'), ((9.020000457763672, 10.399999618530273), 'The event'), ((10.399999618530273, 10.979999542236328), "we'll explore"), ((10.979999542236328, 11.579999923706055), 'today is'), ((11.579999923706055, 12.100000381469727), 'Operation'), ((12.100000381469727, 12.819999694824219), 'Bertrand a'), ((12.819999694824219, 13.640000343322754), 'masterclass in'), ((13.640000343322754, 13.979999542236328), 'military'), ((13.979999542236328, 14.619999885559082), 'subterfuge'), ((14.619999885559082, 15.199999809265137), 'carried out'), ((15.199999809265137, 15.720000267028809), 'by the British'), ((15.720000267028809, 16.399999618530273), 'forces in'), ((16.399999618530273, 18.440000534057617), '1942 As'), ((18.440000534057617, 18.860000610351562), 'the German'), ((18.860000610351562, 19.65999984741211), 'Afrika Korps'), ((19.65999984741211, 20.739999771118164), 'led by the'), ((20.739999771118164, 20.739999771118164), 'renowned'), ((20.739999771118164, 21.559999465942383), 'General Erwin'), ((21.559999465942383, 21.700000762939453), 'Rommel'), ((21.700000762939453, 22.65999984741211), 'fortified their'), ((22.65999984741211, 23.31999969482422), 'positions in'), ((23.31999969482422, 23.860000610351562), 'North Africa'), ((23.860000610351562, 24.579999923706055), 'the Allies'), ((24.579999923706055, 25.360000610351562), 'faced a'), ((25.360000610351562, 25.360000610351562), 'daunting'), ((25.360000610351562, 26.920000076293945), 'challenge To'), ((26.920000076293945, 27.700000762939453), 'succeed they'), ((27.700000762939453, 28.440000534057617), 'needed to'), ((28.440000534057617, 28.799999237060547), 'strike a'), ((28.799999237060547, 29.280000686645508), 'blow that'), ((29.280000686645508, 29.559999465942383), "Rommel wouldn't"), ((29.559999465942383, 30.139999389648438), 'see coming'), ((30.139999389648438, 31.3799991607666), 'Enter'), ((31.3799991607666, 31.84000015258789), 'Lieutenant'), ((31.84000015258789, 32.560001373291016), 'Colonel Dudley'), ((32.560001373291016, 33.2599983215332), 'Clark a'), ((33.2599983215332, 34.0), 'mastermind in'), ((34.0, 35.560001373291016), 'deception With'), ((35.560001373291016, 35.939998626708984), 'the fate'), ((35.939998626708984, 36.459999084472656), 'of the North'), ((36.459999084472656, 36.880001068115234), 'African'), ((36.880001068115234, 37.36000061035156), 'campaign'), ((37.36000061035156, 37.84000015258789), 'hanging in'), ((37.84000015258789, 38.2599983215332), 'the balance'), ((38.2599983215332, 39.13999938964844), 'Clark devised'), ((39.13999938964844, 39.619998931884766), 'a brilliant'), ((39.619998931884766, 40.2400016784668), 'plan to'), ((40.2400016784668, 40.70000076293945), 'disguise the'), ((40.70000076293945, 41.459999084472656), 'actual location'), ((41.459999084472656, 42.15999984741211), 'of the Allied'), ((42.15999984741211, 42.7400016784668), 'attack during'), ((42.7400016784668, 43.29999923706055), 'the Second'), ((43.29999923706055, 43.720001220703125), 'Battle of'), ((43.720001220703125, 44.34000015258789), 'El Alamein'), ((44.34000015258789, 45.84000015258789), 'Operation'), ((45.84000015258789, 46.220001220703125), 'Bertrand'), ((46.220001220703125, 46.939998626708984), 'revolved around'), ((46.939998626708984, 47.459999084472656), 'the creation'), ((47.459999084472656, 48.20000076293945), 'of a vast'), ((48.20000076293945, 48.880001068115234), 'phantom army'), ((48.880001068115234, 49.459999084472656), 'in the south'), ((49.459999084472656, 49.939998626708984), 'while the'), ((49.939998626708984, 50.619998931884766), 'attack would'), ((50.619998931884766, 51.02000045776367), 'come from'), ((51.02000045776367, 51.439998626708984), 'the north'), ((51.439998626708984, 53.060001373291016), 'Real artillery'), ((53.060001373291016, 53.900001525878906), 'was disguised'), ((53.900001525878906, 54.380001068115234), 'as trucks'), ((54.380001068115234, 55.02000045776367), 'using wooden'), ((55.02000045776367, 55.65999984741211), 'frames and'), ((55.65999984741211, 56.36000061035156), 'paint tanks'), ((56.36000061035156, 56.79999923706055), 'were hidden'), ((56.79999923706055, 57.34000015258789), 'in sunken'), ((57.34000015258789, 57.939998626708984), 'holes covered'), ((57.939998626708984, 58.70000076293945), 'with deceptive'), ((58.70000076293945, 59.380001068115234), 'netting and'), ((59.380001068115234, 59.79999923706055), 'dummy tanks'), ((59.79999923706055, 60.36000061035156), 'made from'), ((60.36000061035156, 60.97999954223633), 'wooden canvas'), ((60.97999954223633, 61.47999954223633), 'were placed'), ((61.47999954223633, 62.15999984741211), 'visibly in'), ((62.15999984741211, 62.599998474121094), 'areas meant'), ((62.599998474121094, 63.15999984741211), 'to mislead'), ((63.15999984741211, 64.5999984741211), 'Even the'), ((64.5999984741211, 64.95999908447266), 'meals of'), ((64.95999908447266, 65.5199966430664), 'the fictitious'), ((65.5199966430664, 66.08000183105469), 'troops were'), ((66.08000183105469, 66.63999938964844), 'orchestrated'), ((66.63999938964844, 67.30000305175781), 'with food'), ((67.30000305175781, 67.81999969482422), 'deliberately'), ((67.81999969482422, 68.45999908447266), 'cooked in'), ((68.45999908447266, 69.05999755859375), 'areas devoid'), ((69.05999755859375, 69.55999755859375), 'of soldiers'), ((69.55999755859375, 70.08000183105469), 'to further'), ((70.08000183105469, 70.5999984741211), 'add to the'), ((70.5999984741211, 70.9000015258789), 'illusion'), ((70.9000015258789, 72.5), 'Meanwhile'), ((72.5, 73.08000183105469), 'tracks were'), ((73.08000183105469, 73.63999938964844), 'meticulously'), ((73.63999938964844, 74.5), 'constructed to'), ((74.5, 74.9800033569336), 'lead the'), ((74.9800033569336, 75.55999755859375), 'Germans into'), ((75.55999755859375, 76.12000274658203), 'believing that'), ((76.12000274658203, 76.80000305175781), 'an army was'), ((76.80000305175781, 77.41999816894531), 'amassing in'), ((77.41999816894531, 77.83999633789062), 'one place'), ((77.83999633789062, 78.31999969482422), 'while the'), ((78.31999969482422, 78.83999633789062), 'real forces'), ((78.83999633789062, 79.30000305175781), 'quietly'), ((79.30000305175781, 79.76000213623047), 'prepared'), ((79.76000213623047, 81.41999816894531), 'elsewhere As'), ((81.41999816894531, 82.08000183105469), 'the sun rose'), ((82.08000183105469, 82.5999984741211), 'on the morning'), ((82.5999984741211, 83.08000183105469), 'of October'), ((83.08000183105469, 84.87999725341797), '23 1942'), ((84.87999725341797, 85.5), 'Rommel and'), ((85.5, 85.95999908447266), 'his forces'), ((85.95999908447266, 86.31999969482422), 'found'), ((86.31999969482422, 86.83999633789062), 'themselves'), ((86.83999633789062, 87.44000244140625), 'duped by'), ((87.44000244140625, 88.08000183105469), "Clark's grand"), ((88.08000183105469, 89.58000183105469), 'illusion The'), ((89.58000183105469, 90.12000274658203), 'real thrust'), ((90.12000274658203, 90.73999786376953), 'of the Allied'), ((90.73999786376953, 91.44000244140625), 'attack emerged'), ((91.44000244140625, 92.05999755859375), 'from the'), ((92.05999755859375, 92.58000183105469), 'north catching'), ((92.58000183105469, 93.0999984741211), 'the Germans'), ((93.0999984741211, 93.62000274658203), 'off guard'), ((93.62000274658203, 94.33999633789062), 'and ultimately'), ((94.33999633789062, 94.94000244140625), 'leading to'), ((94.94000244140625, 95.5199966430664), 'a decisive'), ((95.5199966430664, 96.0999984741211), 'victory at'), ((96.0999984741211, 96.77999877929688), 'El Alamein'), ((96.77999877929688, 98.5), 'This ingenious'), ((98.5, 99.31999969482422), 'masquerade not'), ((99.31999969482422, 99.86000061035156), 'only marked'), ((99.86000061035156, 100.27999877929688), 'a turning'), ((100.27999877929688, 100.86000061035156), 'point in'), ((100.86000061035156, 101.26000213623047), 'the North'), ((101.26000213623047, 101.66000366210938), 'African'), ((101.66000366210938, 102.41999816894531), 'campaign but'), ((102.41999816894531, 102.94000244140625), 'also'), ((102.94000244140625, 103.55999755859375), 'highlighted the'), ((103.55999755859375, 104.12000274658203), 'power of'), ((104.12000274658203, 104.9800033569336), 'deception in'), ((104.9800033569336, 104.9800033569336), 'warfare'), ((104.9800033569336, 106.5), 'Operation'), ((106.5, 106.86000061035156), 'Bertrand'), ((106.86000061035156, 107.54000091552734), 'remains a'), ((107.54000091552734, 107.9800033569336), 'testament to'), ((107.9800033569336, 108.87999725341797), 'how cunning'), ((108.87999725341797, 109.63999938964844), 'can outmaneuver'), ((109.63999938964844, 110.31999969482422), 'brute strength'), ((110.31999969482422, 110.91999816894531), 'forever'), ((110.91999816894531, 111.55999755859375), 'changing the'), ((111.55999755859375, 112.30000305175781), 'battlefield and'), ((112.30000305175781, 112.72000122070312), 'illustrating'), ((112.72000122070312, 113.5999984741211), 'that sometimes'), ((113.5999984741211, 114.36000061035156), 'victory comes'), ((114.36000061035156, 114.80000305175781), 'not from'), ((114.80000305175781, 115.22000122070312), 'the force'), ((115.22000122070312, 115.9800033569336), 'of arms but'), ((115.9800033569336, 116.33999633789062), 'from the'), ((116.33999633789062, 116.69999694824219), 'art of'), ((116.69999694824219, 116.91999816894531), 'illusion')]

        self._db_timed_video_searches = [[[0.0, 5.659999847412109], ['World War', 'History', '1940s']], [[5.659999847412109, 11.579999923706055], ['Military deception', 'Operation Bertrand', 'Military strategy']], [[11.579999923706055, 17.25999984741211], ['German Afrika Korps', 'General Erwin Rommel', 'British forces']], [[17.25999984741211, 23.860000610351562], ['North Africa campaign', 'Allied forces', 'German fortifications']], [[23.860000610351562, 30.139999389648438], ['Allied attack', 'Battle of El Alamein', 'Military tactics']], [[30.139999389648438, 37.36000061035156], ['Lieutenant Colonel Dudley Clark', 'British military', 'Deception plan']], [[37.36000061035156, 46.939998626708984], ['Phantom army', 'Disguised artillery', 'Military camouflage']], [[46.939998626708984, 56.36000061035156], ['Dummy tanks', 'Wooden canvas', 'Military ruse']], [[56.36000061035156, 64.5999984741211], ['Artillery deception', 'Truck camouflage', 'Military tactics']], [[64.5999984741211, 70.9000015258789], ['Illusionary troops', 'Fictitious soldiers', 'Decoy strategy']], [[70.9000015258789, 79.30000305175781], ['Deceptive netting', 'Misleading tactics', 'Military trickery']], [[79.30000305175781, 88.08000183105469], ['Masquerade strategy', 'Illusion technique', 'Military genius']], [[88.08000183105469, 94.33999633789062], ['Allied victory', 'German defeat', 'Strategic triumph']], [[94.33999633789062, 104.9800033569336], ['Power of deception', 'Cunning over strength', 'Tactical warfare']], [[104.9800033569336, 116.91999816894531], ['Battlefield illusion', 'Victory strategy', 'Art of warfare']]]

        self._db_timed_video_urls = [[[0.0, 5.659999847412109], 'videos/image_to_video/video_1728207302.mp4'], [[5.659999847412109, 11.579999923706055], 'videos/image_to_video/video_1728207376.mp4'], [[11.579999923706055, 17.25999984741211], 'videos/image_to_video/video_1728207462.mp4'], [[17.25999984741211, 23.860000610351562], 'videos/image_to_video/video_1728207524.mp4'], [[23.860000610351562, 30.139999389648438], 'videos/image_to_video/video_1728207627.mp4'], [[30.139999389648438, 37.36000061035156], 'videos/image_to_video/video_1728207742.mp4'], [[37.36000061035156, 46.939998626708984], 'videos/image_to_video/video_1728207820.mp4'], [[46.939998626708984, 56.36000061035156], 'videos/image_to_video/video_1728207922.mp4'], [[56.36000061035156, 64.5999984741211], 'videos/image_to_video/video_1728208044.mp4'], [[64.5999984741211, 70.9000015258789], 'videos/image_to_video/video_1728208144.mp4'], [[70.9000015258789, 79.30000305175781], 'videos/image_to_video/video_1728208252.mp4'], [[79.30000305175781, 88.08000183105469], 'videos/image_to_video/video_1728208359.mp4'], [[94.33999633789062, 104.9800033569336], 'videos/image_to_video/video_1728208479.mp4'], [[104.9800033569336, 116.91999816894531], 'videos/image_to_video/video_1728208581.mp4']]

        self._db_background_music_url = "/app/public/trimmed_1728208666.wav"
        self._db_audio_path = ".editing_assets/general_video_assets/6136eb114f5f40d8a671f455/temp_audio_path.wav"
        self._db_voiceover_duration = 117.912

    def _generateTempAudio(self):
        pass

    def _speedUpAudio(self):
        pass

    def _timeCaptions(self):
        pass

    def _generateVideoSearchTerms(self):
        pass

    def _generateVideoUrls(self):
        pass

    def _chooseBackgroundMusic(self):
        pass

    def _prepareBackgroundAssets(self):
        pass

    def _prepareCustomAssets(self):
        pass

    def _editAndRenderShort(self):
        # Verify required parameters
        self.verifyParameters(voiceover_audio_url=self._db_audio_path)

        outputPath = os.path.join(self.dynamicAssetDir, "rendered_video.mp4")

        transition_duration = 1
        filter_complex_parts = []
        ffmpeg_input_args = []
        previous_offset = 0

        # Create the input arguments and filter complex parts
        for index, ((t1, t2), video_url) in enumerate(self._db_timed_video_urls):
            # Convert to absolute path
            absolute_video_path = os.path.abspath(video_url)
            ffmpeg_input_args.extend(['-i', absolute_video_path])  # Add each input separately

            # Construct xfade transitions
            if index > 0:  # Only start adding xfade after the first video
                offset = math.floor((((t2 - t1) + previous_offset) - transition_duration))   # Set offset to the start of current video
                previous_offset = offset
                # Create a filter for xfade between the previous video and the current video
                filter_complex_parts.append(f"xfade=transition=fade:duration={transition_duration}:offset={offset}")

        # Join all parts of the filter complex with commas
        filter_complex = ",".join(filter_complex_parts)

        logger.info(f"filter_complex: {filter_complex}")

        # Construct the final ffmpeg command
        ffmpeg_command = [
            'ffmpeg',
        ] + ffmpeg_input_args + [
            '-filter_complex', filter_complex,
            '-y', outputPath  # Overwrite output file if it exists
        ]

        logger.info(f"ffmpeg_command: {ffmpeg_command}")

        # Run the ffmpeg command and log any errors
        try:
            result = subprocess.run(ffmpeg_command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            if result.returncode != 0:
                logger.info(f"FFmpeg error: {result.stderr}")
            else:
                logger.info(f"Video created successfully at {outputPath}")
        except Exception as e:
            logger.info(f"Error running FFmpeg: {e}")

        # Save the final video path
        self._db_video_path = outputPath

    def _addMetadata(self):
        if not os.path.exists('videos/'):
            os.makedirs('videos')
        self._db_yt_title, self._db_yt_description = gpt_yt.generate_title_description_dict(self._db_script)

        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        newFileName = f"videos/{date_str} - " + \
            re.sub(r"[^a-zA-Z0-9 '\n\.]", '', self._db_yt_title)

        shutil.move(self._db_video_path, newFileName+".mp4")
        with open(newFileName+".txt", "w", encoding="utf-8") as f:
            f.write(
                f"---Youtube title---\n{self._db_yt_title}\n---Youtube description---\n{self._db_yt_description}")
        self._db_video_path = newFileName+".mp4"
        self._db_ready_to_upload = True
