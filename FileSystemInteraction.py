import os
import glob
import winshell # type: ignore
import subprocess



class JarvisFileInteraction:
    def __init__(self):
        self.current_directory = os.getcwd()
        shortcuts_folder = '../shortcuts'
        self.home_directory = os.path.expanduser('~')

    def change_directory(self, path):
        path = self.resolve_shortcut(path)
        if os.path.isdir(path):
            self.current_directory = path
            return f"Changed directory to {path}"
        else:
            # Check in home directory
            home_path = os.path.join(self.home_directory, path)
            if os.path.isdir(home_path):
                self.current_directory = home_path
                return f"Changed directory to {home_path}"
            # Search for the directory across the computer
            for root, dirs, files in os.walk("/"):
                if path in dirs:
                    found_path = os.path.join(root, path)
                    self.current_directory = found_path
                    return f"Changed directory to {found_path}"
            return "Directory does not exist."
        
    def open_directory(self, path):
        # path = self.resolve_shortcut(path)
        # if os.path.isdir(path):
        #     subprocess.Popen(f'explorer /select,"{path}"')
        #     return f"Opened directory {path} in file explorer."
        # else:
            # Check in home directory
            home_path = os.path.join(self.home_directory, path)
            if os.path.isdir(home_path):
                print('HOME PATH>>>>>>', home_path)
                subprocess.Popen(f'explorer /select,"{home_path}"')
                print('OPENED HOME PATH>>>>>>', home_path)
                return f"Opened directory {home_path} in file explorer."
            # Search for the directory across the computer
            for root, dirs, files in os.walk("/"):
                if path in dirs:
                    found_path = os.path.join(root, path)
                    subprocess.Popen(f'explorer /select,"{found_path}"')
                    return f"Opened directory {found_path} in file explorer."
            return "Directory does not exist."

    def list_files(self):
        try:
            files = os.listdir(self.current_directory)
            return files
        except Exception as e:
            return str(e)

    def read_file(self, filename):
        # Check if file exists directly
        file_path = os.path.join(self.current_directory, filename)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as f:
                    return f.read()
            except Exception as e:
                return str(e)
        else:
            # Check for matching files with different extensions
            for ext in ['', '.txt', '.docx', '.pdf', '.csv']:  # Add more extensions as needed
                file_path_ext = file_path + ext
                if os.path.isfile(file_path_ext):
                    try:
                        with open(file_path_ext, 'r') as f:
                            return f.read()
                    except Exception as e:
                        return str(e)
        return "File does not exist."

    def create_file(self, filename, content=""):
        try:
            with open(os.path.join(self.current_directory, filename), 'w') as f:
                f.write(content)
            return f"File {filename} created."
        except Exception as e:
            return str(e)

    def write_to_file(self, filename, content):
        try:
            with open(os.path.join(self.current_directory, filename), 'a') as f:
                f.write(content)
            return f"Content written to {filename}."
        except Exception as e:
            return str(e)

    def search_files(self, pattern):
        try:
            files = glob.glob(os.path.join(self.current_directory, pattern))
            return files
        except Exception as e:
            return str(e)

    def delete_file(self, filename):
        try:
            os.remove(os.path.join(self.current_directory, filename))
            return f"File {filename} deleted."
        except Exception as e:
            return str(e)
