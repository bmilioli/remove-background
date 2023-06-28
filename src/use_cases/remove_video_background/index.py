import imageio
import base64
import os
import requests
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
import tempfile
from typing import List
from PIL import Image
import glob
import numpy as np
import moviepy.editor as mpy
import cv2


from config import settings


class RemoveVideobackground:

    def process_remove_video_background(self, video_file: UploadFile) -> FileResponse:
        fps_video = self._extract_frames_from_video(video_file)
        self._remove_background_from_video()
        return self._create_video_from_frames(fps_video)

    def _extract_frames_from_video(self, video: UploadFile) -> int:
        # Verificar se foi fornecido um arquivo de vídeo
        if not video.filename.endswith(('.mp4', '.avi', '.mkv')):
            raise HTTPException(status_code=400, detail="Invalid video format")

        # Criar um diretório para armazenar os frames
        os.makedirs('temp/frames', exist_ok=True)

        # Salvar o arquivo de vídeo
        video_path = os.path.join('temp/frames', video.filename)
        with open(video_path, 'wb') as f:
            while True:
                # Ler os dados do arquivo em chunks
                chunk = video.file.read(4096)
                if not chunk:
                    # Todos os dados foram lidos, sair do loop
                    break
                # Escrever os dados no arquivo
                f.write(chunk)
                # Flush para garantir a gravação imediata no disco
                f.flush()

        # salvas os frams em png

        # Abrir o vídeo para leitura
        video_capture = cv2.VideoCapture(video_path)

        # Obter algumas informações do vídeo
        fps = video_capture.get(cv2.CAP_PROP_FPS)
        total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))

        # Loop para extrair os frames
        for frame_index in range(total_frames):
            # Ler o próximo frame
            success, frame = video_capture.read()
            if not success:
                break

            # Salvar o frame como arquivo PNG
            frame_filename = f"frame_{frame_index:04d}.png"
            frame_path = os.path.join('temp/frames', frame_filename)
            cv2.imwrite(frame_path, frame)

        # Fechar o vídeo
        video_capture.release()

        return fps

    def _remove_background_from_video(self, model: str = 'u2net') -> List[str]:
        input_folder = "temp/frames"
        output_folder = "temp/processed"
        url = "http://127.0.0.1:7860/rembg"
        # Verifica se a pasta de saída existe, senão cria
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        frameNumber = 1
        processed_images = []

        # Lista os arquivos da pasta de entrada
        for filename in os.listdir(input_folder):
            if filename.endswith(".png") or filename.endswith(".jpg"):
                # Carrega a imagem
                image_path = os.path.join(input_folder, filename)
                with open(image_path, "rb") as image_file:
                    image = image_file.read()
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
                    processed_image_bytes = base64.b64decode(
                        response.json()["image"])

                    # Salvar a imagem processada em um arquivo png
                    processed_image_path = f'{output_folder}/image{frameNumber}.png'
                    with open(processed_image_path, 'wb') as f:
                        f.write(processed_image_bytes)

                    processed_images.append(processed_image_path)
                    frameNumber += 1

                else:
                    raise HTTPException(
                        status_code=response.status_code, detail="Error processing the image")

        return processed_images

    def _create_video_from_frames(self, fps: int) -> FileResponse:

        # Criar um diretório para armazenar o vídeo
        os.makedirs('temp/video', exist_ok=True)

        # Abrir o diretório de frames original
        frames_path_original = os.path.join('temp/frames', '*.png')
        frame_files_original = sorted(glob.glob(frames_path_original))

        # Abrir o diretório de frames
        frames_path = os.path.join('temp/processed', '*.png')
        frame_files = sorted(glob.glob(frames_path))

        # Obter a largura e altura do primeiro frame
        first_frame_original = Image.open(frame_files_original[0])
        width, height = first_frame_original.size

        # Determinar a proporção original do vídeo
        aspect_ratio = width / height

        # Determinar a nova largura com base na altura fixa (por exemplo, 480 pixels)
        new_height = 480
        new_width = int(new_height * aspect_ratio)

        # Criar um arquivo de vídeo
        video_path = os.path.join('temp/video', 'video.mp4')
        writer = imageio.get_writer(video_path, fps=fps)

        # Adicionar os frames ao vídeo com redimensionamento
        for frame_file in frame_files:
            frame = Image.open(frame_file)

            frame_resized = frame.resize((new_width, new_height))
            writer.append_data(np.array(frame_resized))

        writer.close()

        # Ler o arquivo de vídeo
        with open(video_path, 'rb') as f:
            video_bytes = f.read()

        return FileResponse(video_bytes, media_type='video/mp4', filename='video.mp4')
