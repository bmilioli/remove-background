from fastapi import FastAPI, UploadFile, File, HTTPException
import imageio
import os

app = FastAPI()

@app.post("/extract_frames")
async def extract_frames(video: UploadFile = File(...)):
    # Verificar se foi fornecido um arquivo de vídeo
    if not video.filename.endswith(('.mp4', '.avi', '.mkv')):
        raise HTTPException(status_code=400, detail="Invalid video format")
    
    # Criar um diretório para armazenar os frames
    os.makedirs('frames', exist_ok=True)
    
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

@app.post("/join_frames")
async def join_frames(frames: list[UploadFile] = File(...)):
    # Verificar se foram fornecidos arquivos de imagem
    for frame in frames:
        if not frame.filename.endswith(('.png', '.jpg', '.jpeg')):
            raise HTTPException(status_code=400, detail="Invalid image format")
    
    # Criar um diretório para armazenar o vídeo
    os.makedirs('videos', exist_ok=True)
    
    # Salvar os arquivos de imagem
    for frame in frames:
        frame_path = os.path.join('videos', frame.filename)
        with open(frame_path, 'wb') as f:
            f.write(frame.file.read())
    
    # Criar um vídeo com os arquivos de imagem
    writer = imageio.get_writer('video.mp4', fps=24)
    for frame in frames:
        frame_path = os.path.join('videos', frame.filename)
        writer.append_data(imageio.imread(frame_path))
    writer.close()
    
    return {"message": "Frames joined successfully"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
