import os

class Config:
    SECRET_KEY = 'tanujach8090'  # you can use secrets.token_hex(16)
    SQLALCHEMY_DATABASE_URI = 'postgresql://myuser:8090@localhost/finance_tracker'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
