from dotenv import load_dotenv
import os

class Config:
    STABLE_DIFFUSION_BASE_URL = os.getenv('STABLE_DIFFUSION_BASE_URL')

settings = Config()