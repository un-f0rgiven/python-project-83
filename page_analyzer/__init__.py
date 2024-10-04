from dotenv import load_dotenv
import os
from page_analyzer.app import app

load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

@app.route('/secret')
def secret():
    return "The key to that chain is in the bathtub"

__all__ = ['app']