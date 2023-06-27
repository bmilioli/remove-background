import imageio
import base64
import os
import requests
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
import tempfile
from typing import List
from PIL import Image

from config import settings

class RemoveVideobackground:

    def process_remove_video_background(self, video_file: UploadFile) -> FileResponse:
        self._extract_frames_from_video(video_file)
        self._remove_background_from_video()
        
        return {"message": "Background removed successfully"}

    def _extract_frames_from_video(video: UploadFile) -> List[str]:
         # Verificar se foi fornecido um arquivo de vídeo
        if not video.filename.endswith(('.mp4', '.avi', '.mkv')):
            raise HTTPException(status_code=400, detail="Invalid video format")
    
        # Criar um diretório para armazenar os frames
        os.makedirs('temp/frames', exist_ok=True)
    
        # Salvar o arquivo de vídeo
        video_path = os.path.join('frames', video.filename)
        with open(video_path, 'wb') as f:
            f.write(video.file.read())
    
        # Extrair os frames do vídeo
        reader = imageio.get_reader(video_path, 'ffmpeg')
        frames = []
        for frame in reader:
            frames.append(frame)
        reader.close()
    
        # Salvar os frames como imagens PNG
        for i, frame in enumerate(frames):
            frame_path = os.path.join('frames', f'frame_{i}.png')
            imageio.imwrite(frame_path, frame)
    
        return {"message": "Frames extracted successfully"}     

    def _remove_background_from_video(model: str = 'u2net') -> List[str]:
        input_folder = "temp/frames"
        output_folder = "temp/processed"
        url = "http://127.0.0.1:7860/rembg"  
        # Verifica se a pasta de saída existe, senão cria
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        frameNumber = 1

        # Lista os arquivos da pasta de entrada
        for filename in os.listdir(input_folder):
            if filename.endswith(".png") or filename.endswith(".jpg"):
                # Carrega a imagem
                image_path = os.path.join(input_folder, filename)
                image = Image.open(image_path)
                # Converte a imagem para base64
                image_base64 = base64.b64encode(image).decode("utf-8")
                # Parâmetros da solicitação para a API rembg
                data = {
                    "input_image": image_base64,
                    "model": "u2net",
                    "return_mask": False,
                     "alpha_matting": False,
                    "alpha_matting_foreground_threshold": 240,
                    "alpha_matting_background_threshold": 10,
                    "alpha_matting_erode_size": 10
                }
                response = requests.post(url, json=data)
                # Verificar a resposta
                if response.status_code == 200:                  
                                        
                    # Decodificar a imagem processada de base64 para bytes
                    processed_image_bytes = base64.b64decode(response.json()["image"])
                    
                    # Salvar a imagem processada em um arquivo PNG
                    processed_image_path = 'output_folder/image{frameNumber}.png'
                    with open(processed_image_path, 'wb') as f:
                        f.write(processed_image_bytes)
                    frameNumber += 1
                    
                    return {"processed_image_path": processed_image_path}
                else:
                    raise HTTPException(status_code=response.status_code, detail="Error processing the image")
    
        return {"message": "Background removed successfully"}

                     
       
        
