import os
import glob
import winshell # type: ignore
import subprocess
import datetime
import python_weather
import asyncio
from sqlalchemy import func
from db import Session, FileIndex


class JarvisFileInteraction:
    def __init__(self, exe_paths=None):
        self.current_directory = os.getcwd()
        shortcuts_folder = '../shortcuts'
        self.home_directory = os.path.expanduser('~')
        self.exe_paths = exe_paths or []
    def open_directory(self, directory_name: str) -> str:
        """
        Search the database for a directory matching `directory_name` and open it in File Explorer.
        Only uses DB info; no filesystem fallbacks.
        """
        session = Session()
        # case-insensitive match for directory names containing the query
        pat = f"%{directory_name.strip()}%"
        match = (
            session.query(FileIndex.path)
                   .filter(
                       FileIndex.is_dir.is_(True),
                       func.lower(FileIndex.path).like(pat.lower())
                   )
                   .first()
        )
        if not match:
            return f"Directory '{directory_name}' not found in index."

        path = match[0]
        try:
            subprocess.Popen(f'explorer /select,"{path}"')
            return f"Opened directory {path} in File Explorer."
        except Exception as e:
            return str(e)

    def search_files(self, pattern: str) -> list:
        """
        Use pure database logic to return a list of file paths matching `pattern`.
        No filesystem fallback.
        """
        session = Session()
        pat = f"%{pattern.strip()}%"
        rows = (
            session.query(FileIndex.path)
                   .filter(
                       FileIndex.is_dir.is_(False),
                       func.lower(FileIndex.path).like(pat.lower())
                   )
                   .limit(20)
                   .all()
        )
        return [r[0] for r in rows]

    def delete_file(self, filename: str) -> str:
        """
        Delete the file at the path found in the database matching `filename`,
        then remove its entry from the index.
        Only uses DB info.
        """
        session = Session()
        pat = f"%{filename.strip()}%"
        match = (
            session.query(FileIndex.path)
                   .filter(
                       FileIndex.is_dir.is_(False),
                       func.lower(FileIndex.path).like(pat.lower())
                   )
                   .first()
        )
        if not match:
            return f"File '{filename}' not found in index."

        path = match[0]
        try:
            os.remove(path)
        except Exception as e:
            return f"Error deleting file: {e}"
    
    def open_file(self, filename: str) -> str:
        """
        Look up `filename` in the file_index, then launch it
        in its default application (Notepad for .txt, Word for .docx, VSCode for .py, etc).
        """
        session = Session()
        pat = f"%{filename.strip()}%"
        # find the first non-directory whose path contains the query
        match = (
            session.query(FileIndex.path)
                   .filter(
                       FileIndex.is_dir.is_(False),
                       func.lower(FileIndex.path).like(pat.lower())
                   )
                   .first()
        )
        if not match:
            return f"File '{filename}' not found in index."

        path = match[0]
        try:
            # On Windows this opens the file with its associated app.
            os.startfile(path)
            return f"Opened file {path} in its default application."
        except AttributeError:
            # os.startfile only exists on Windows—fall back if you ever run cross-platform:
            try:
                if os.name == "posix":
                    subprocess.Popen(["xdg-open", path])
                else:
                    subprocess.Popen(["open", path])  # macOS
                return f"Opened file {path} with system default."
            except Exception as e:
                return f"Error opening file: {e}"
        except Exception as e:
            return f"Error opening file: {e}"
    
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