from fastapi import APIRouter, status

background_remover = APIRouter()

@background_remover.post('/remove_background', status_code=status.HTTP_201_CREATED, description='Removes background from video')
def remove_background():
    return {'message': 'Background removed successfully'}

@background_remover.post('/first_frame', status_code=status.HTTP_201_CREATED, description='Returns the first frame of the video')
def first_frame_of_video():
    return {'message': 'Background removed successfully'}