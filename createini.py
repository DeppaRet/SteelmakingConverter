from configparser import ConfigParser

config = ConfigParser()

config['DBsettings'] = {
    'DBhost': 'localhost',
    'login': 'root',
    'password': 'root'
}
with open('./dev.ini', 'w') as f:
    config.write(f)

from configparser import ConfigParser
parser = ConfigParser()
parser.read('dev.ini')

print(parser.sections())
print(parser.get('DBsettings', 'DBhost'))
print(parser.get('DBsettings', 'login'))
print(parser.get('DBsettings', 'password'))

from configparser import ConfigParser

parser = ConfigParser()
sd = 'DBh'
parser.read('dev.ini')
parser.set('DBsettings', 'DBhost', sd)

# Writing our configuration file to 'example.ini'
with open('dev.ini', 'w') as configfile:
    parser.write(configfile)

print(parser.get('DBsettings', 'DBhost'))
print(parser.get('DBsettings', 'login'))
print(parser.get('DBsettings', 'password'))


