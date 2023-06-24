from fastapi import APIRouter, status

background_remover = APIRouter()

@background_remover.post('/remove_background', status_code=status.HTTP_201_CREATED, description='Removes background from video')
def remove_background():
    return {'message': 'Background removed successfully'}