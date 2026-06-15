from configparser import ConfigParser

config = ConfigParser()

config['DBsettings'] = {
    'DBhost': 'localhost',
    'login': 'root',
    'password': 'root',
}
config['AppSettings'] = {
    'theme': 'dark',
    'language': 'ru',
}

with open('./dev.ini', 'w', encoding='utf-8') as f:
    config.write(f)
