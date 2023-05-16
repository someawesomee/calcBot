import configparser


class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read("config.ini", encoding="utf-8")

    def get(self, setting_path, setting_name=''):
        result = False
        if setting_path in self.config:
            if not setting_name == '':
                if setting_name in self.config[setting_path]:
                    result = self.config[setting_path][setting_name]
            else:
                result = self.config[setting_path]
        return result

    def set(self, setting_path, setting_name, new_value):
        result = False
        if setting_path in self.config:
            if setting_name in self.config[setting_path]:
                self.config[setting_path][setting_name] = str(new_value)
                result = True
        return result
