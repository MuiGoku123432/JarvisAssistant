import os
import glob
import winshell # type: ignore
import subprocess
import datetime
import python_weather
import asyncio



class JarvisFileInteraction:
    def __init__(self, exe_paths=None):
        self.current_directory = os.getcwd()
        shortcuts_folder = '../shortcuts'
        self.home_directory = os.path.expanduser('~')
        self.exe_paths = exe_paths or []


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
    def execute_app(self, app_name):
        print('IN EXECUTE!!! APP NAME>>>>>>', app_name)
        # Remove spaces and ensure app_name has .exe extension
        app_name = app_name.replace(' ', '')
        app_name = app_name.replace('.', '')
        app_name = app_name.replace(',', '')
        app_name = app_name.replace('?', '')
        app_name = app_name if app_name.endswith('.exe') else f"{app_name}.exe"
        # Ensure app_name has .exe extension
        # Check in predefined exe paths
        for exe_path in self.exe_paths:
            full_path = os.path.join(exe_path, app_name)
            print('FULL PATH>>>>>>>>>>>' + full_path)
            if os.path.isfile(full_path):
                try:
                    subprocess.Popen([full_path])
                    return f"Executed {app_name} from {full_path}"
                except Exception as e:
                    return str(e)
        return "Application not found."
    
    def get_time(self):
        time = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
        return time
    
    async def weather(self):
        # declare the client. the measuring unit used defaults to the metric system (celcius, km/h, etc.)
        async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
            # fetch a weather forecast from a city
            weather = await client.get('Omaha, AR')

            # # returns the current day's forecast temperature (int)
            # temp = str(weather.temperature)

            # # get the weather forecast for a few days
            # for daily in weather.daily_forecasts:
            #     daily = daily

            # # hourly forecasts
            # for hourly in daily.hourly_forecasts:
            #     hourly = hourly

            # weather = f'The current temperature is {temp} degrees. The next 5 days forecast is {daily} and the next 24 hours forecast is {hourly}'
            return str(weather)
        
    def get_weather(self):
        return asyncio.run(self.weather())