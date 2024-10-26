import os

from fastapi import BackgroundTasks, APIRouter, HTTPException
from pydantic import BaseModel
from app.vid_gen import VidGen
from shortGPT.gpt import gpt_yt
from shortGPT.database.content_database import ContentDatabase
from fastapi.responses import FileResponse
from app.logger import logger
from typing import Literal

router = APIRouter()

content_db = ContentDatabase()

class VidGenRequest(BaseModel):
    prompt:str = None
    script:str = None
    art_style:Literal['normal', 'comic_book', 'disney_toon', 'studio_ghibli', 'childrens_book', 'photo_realism', 'minecraft', 'watercolor', 'expressionism', 'charcoal', 'gtav', 'anime', 'normal_v2'] = 'normal'
    video_duration:Literal['30-60', '60-90'] = '60-90'
    apply_background_music:bool = False

class VideoInfoRequest(BaseModel):
    video_id:str

@router.get("/health")
def health_check():
    return {"status": "Healthy"}

@router.get("/hello")
def hello():
    return {"message": "Hello"}

@router.post("/vid-gen")
async def vid_gen(request: VidGenRequest, background_tasks: BackgroundTasks):
    try:
        vidgen = VidGen(art_style=request.art_style, apply_background_music=request.apply_background_music)

        content_data_manager = content_db.createContentDataManager("general_video")
        video_id = content_data_manager._getId()

        vidgen.video_id = video_id

        script = vidgen.generate_script(request.prompt, video_duration=request.video_duration, script=request.script)

        title, caption = gpt_yt.generate_title_description_dict(script)

        background_tasks.add_task(vidgen.make_video)

        return {
            "video_id": video_id,
            "title": title,
            "caption": caption,
            "script": script
        }
    except Exception as e:
        # Log the error with stack trace
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing the request.")

@router.post("/video-info")
async def video_info(request: VideoInfoRequest):
    try:
        video = content_db.getContentDataManager(request.video_id, "general_video")
        
        if not video:
            raise HTTPException(status_code=404, detail="No video found")
        
        last_completed_step = video.get("last_completed_step") or 0
        total_steps = 10

        data = {
            "id": video.get("_id"),
            "ready_to_upload": video.get("ready_to_upload"),
            "last_completed_step": last_completed_step,
            "total_steps": total_steps,
            "percentage_completed": int((last_completed_step / total_steps) * 100),
            "video_path": video.get("video_path"),
        }
        
        return {"video": data}
    except Exception as e:
        # Log the error with stack trace
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing the request.")

@router.post("/get-video")
async def get_video(request: VideoInfoRequest):
    try:
        video = content_db.getContentDataManager(request.video_id, "general_video")
        
        if not video:
            raise HTTPException(status_code=404, detail="No video found")
        
        video_path = video.get('video_path')

        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video file not found")

        return FileResponse(video_path, media_type="video/mp4")
        
    except Exception as e:
        # Log the error with stack trace
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing the request.")