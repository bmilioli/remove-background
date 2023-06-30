import imageio
import base64
import os
import requests
from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse
import tempfile
from typing import List
from PIL import Image
import glob
import numpy as np
import moviepy.editor as mpy
import cv2
import rembg
from typing import List


from config import settings


class RemoveVideobackground:

    def process_remove_video_background_cpu(self, video_file: UploadFile) -> StreamingResponse:

        fps_video = self._extract_frames_from_video(video_file)
        frame_files = self._remove_background_from_video_cpu()
        self._add_background_to_video()
        return self._create_video_from_frames(24)

    def process_remove_video_background_gpu(self, video_file: UploadFile) -> StreamingResponse:

        fps_video = self._extract_frames_from_video(video_file)
        frame_files = self._remove_background_from_video_gpu()
        self._add_background_to_video()
        return self._create_video_from_frames(24)

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

    def _remove_background_from_video_gpu(self, model: str = 'u2net') -> List[str]:
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

                    # Salvar a imagem processada em um arquivo png com o mesmo nome
                    processed_image_path = f'{output_folder}/frame_{frameNumber:04d}.png'
                    with open(processed_image_path, 'wb') as f:
                        f.write(processed_image_bytes)

                    processed_images.append(processed_image_path)
                    frameNumber += 1

                else:
                    raise HTTPException(
                        status_code=response.status_code, detail="Error processing the image")

        return processed_images

    def _remove_background_from_video_cpu(self) -> List[str]:
        processed_images = []
        frameNumber = 0
        input_folder = "temp/frames"
        output_folder = "temp/processed"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        for filename in os.listdir(input_folder):
            if filename.endswith(".png") or filename.endswith(".jpg"):
                # Carrega a imagem
                image_path = os.path.join(input_folder, filename)
                with open(image_path, "rb") as image_file:
                    image = image_file.read()

                # Remove o fundo usando a biblioteca rembg
                processed_image = rembg.remove(image)

                # Salva a imagem processada em um arquivo png com o mesmo nome
                processed_image_path = os.path.join(
                    output_folder, f"frame_processed_{frameNumber:04d}.png")
                with open(processed_image_path, 'wb') as f:
                    f.write(processed_image)

                processed_images.append(processed_image_path)
                frameNumber += 1

        return processed_images

    # adicionar fundo preto aos frames
    def _add_background_to_video(self) -> List[str]:
        processed_images_with_black = []
        frameNumber = 0
        input_folder = "temp/processed"
        output_folder = "temp/processed_with_background"

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        for filename in os.listdir(input_folder):
            if filename.endswith(".png") or filename.endswith(".jpg"):
                # Carrega a imagem
                image_path = os.path.join(input_folder, filename)
                with Image.open(image_path) as image:
                    # Cria uma nova imagem com fundo preto
                    processed_image_with_black = Image.new(
                        "RGBA", image.size, (0, 0, 0))
                    processed_image_with_black.paste(image, (0, 0), image)

                    # Salva a imagem processada com fundo preto em um arquivo png com o mesmo nome
                    processed_image_path = os.path.join(
                        output_folder, f"frame_processed_{frameNumber:04d}.png")
                    processed_image_with_black.save(processed_image_path)

                    processed_images_with_black.append(processed_image_path)
                    frameNumber += 1

        return processed_images_with_black

    def _create_video_from_frames(self, fps: int) -> StreamingResponse:
        output_folder = 'temp/video'
        input_folder = 'temp/processed_with_background'

        # Criar um diretório para armazenar o vídeo
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Abrir o diretório de frames
        frames_path = os.path.join(input_folder, '*.png')
        frame_files = sorted(glob.glob(frames_path))

        # Obter a largura e altura do primeiro frame
        first_frame = Image.open(frame_files[0])
        width, height = first_frame.size

        # Determinar a proporção original do vídeo
        aspect_ratio = width / height

        # Determinar a nova largura com base na altura desejada
        new_width = int(height * aspect_ratio)

        # Criar um arquivo de vídeo
        video_path = os.path.join(output_folder, 'video.mp4')
        writer = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(
            *'mp4v'), fps, (new_width, height))

        # Adicionar os frames ao vídeo com redimensionamento
        for frame_file in frame_files:
            frame = Image.open(frame_file)
            frame_resized = frame.resize((new_width, height))
            frame_resized_bgr = cv2.cvtColor(
                np.array(frame_resized), cv2.COLOR_RGBA2BGR)
            writer.write(frame_resized_bgr)

        writer.release()

        # Ler o conteúdo do arquivo de vídeo
        with open(video_path, 'rb') as f:
            video_bytes = f.read()

            # Retornar um StreamingResponse com o objeto iterável
        def stream():
            with open(video_path, 'rb') as file:
                while True:
                    data = file.read(4096)
                    if not data:
                        break
                    yield data

        headers = {
            'Content-Disposition': 'attachment; filename=video.mp4'
        }

        return StreamingResponse(stream(), media_type='video/mp4', headers=headers)
