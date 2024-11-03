import tempfile


class Playlist:
    def __init__(self):
        self.files = []

    def new_file(self, suffix='.mp3'):
        file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        self.files.append(file.name)
        return self.files[-1]

    def get_files(self):
        return self.files
