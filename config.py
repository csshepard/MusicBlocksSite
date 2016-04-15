
class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = "A\xd5p\xa3\xda\xef\x9esL\x0e\xb1\xe0\x91\xba\xc2\x90\xbeb\xb4\x84\xb0jA\xdd"
    SQLALCHEMY_DATABASE_URI = "sqlite:////home/pi/MusicBlocks/MusicBlocks.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PATH = "/home/pi/MusicBlocks"

class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:////home/chris/Projects/MusicBlocks/MusicBlocks.db"
    PATH = "/home/chris/Projects/MusicBlocks"

class TestingConfig(Config):
    TESTING = True
