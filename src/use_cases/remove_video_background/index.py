import imageio
import base64
import os
import requests
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
import tempfile
from typing import List

from config import settings

class RemoveVideobackground:
    def process_remove_video_background(self, video_file: UploadFile) -> FileResponse:
        base64_frames_list = self._video_to_base64_frames_list(video_file)
        processed_frames = self._remove_background_from_list_of_frames(base64_frames_list)
        processed_video_output = self._base64_frames_list_to_video(processed_frames)

        return processed_video_output

    def _video_to_base64_frames_list(self, video_file: UploadFile) -> List[str]:
        base64_frames_list = []

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True, dir="temp") as temp_file:
            video_path = temp_file.name
            temp_file.write(video_file.file.read())
            reader = imageio.get_reader(video_path, 'ffmpeg')

            for frame in reader:
                buffer = imageio.imwrite(imageio.RETURN_BYTES, frame, format='JPEG')
                base64_frame = base64.b64encode(buffer)
                base64_frames_list.append(base64_frame.decode('utf-8'))
            reader.close()
        
        return base64_frames_list

    def _base64_frames_list_to_video(self, base64_frame_list: List[str]) -> str:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False, dir="temp") as temp_file:
            output_path = temp_file.name
            writer = imageio.get_writer(temp_file.name, fps=24)

            for frame in base64_frame_list:
                buffer = base64.b64decode(frame)
                writer.append_data(imageio.imread(buffer, format='JPEG'))
            writer.close()
        
        return output_path

    def _remove_background_from_list_of_frames(self, base64_frames_list: List[str], model:str = 'u2net') -> List[str]:
        stable_diffusion_api_url = "http://127.0.0.1:7860/rembg"

        processed_frames = []
        
        for frame in base64_frames_list:
            data = {
                "input_image": frame,
                "model": model,
                "return_mask": False,
                "alpha_matting": False,
                "alpha_matting_foreground_threshold": 240,
                "alpha_matting_background_threshold": 10,
                "alpha_matting_erode_size": 10
            }

            response = requests.post(stable_diffusion_api_url, json=data)
        
            if response.status_code == 200:
                response = response.json()
                processed_frames.append(response["image"])
            else:
                raise HTTPException(status_code=500, detail="Internal server error")
            
               
        return processed_frames
