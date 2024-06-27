import re
from FileSystemInteraction import JarvisFileInteraction

class JarvisAssistant:
    def __init__(self):
        self.file_interaction = JarvisFileInteraction()

    def parse_command(self, command):
        # Define regex patterns for different commands
        commands = {
            "change_directory": r"(change directory to) (.+)",
            "open_directory": r"(open) (.+)",
            "list_files": r"(list files|show files|what's here)",
            "read_file": r"(read file) (.+)",
            "create_file": r"(create file|new file) (.+)",
            "write_to_file": r"(write to file) (.+) with content (.+)",
            "search_files": r"(search files for|find files) (.+)",
            "delete_file": r"(delete file|remove file) (.+)"
        }

        for action, pattern in commands.items():
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return action, match.groups() if match.groups() else (None,)
        
        return None, None
    def execute_command(self, command):
        action, params = self.parse_command(command)
        print('ACTION>>>>>>', action)
        print('PARAMS>>>>>>', params)
        if action:
            try:
                if action == "change_directory":
                    response = self.file_interaction.change_directory(params[1])
                elif action == "open_directory":
                    response = self.file_interaction.open_directory(params[1])
                elif action == "list_files":
                    response = self.file_interaction.list_files()
                elif action == "read_file":
                    response = self.file_interaction.read_file(params[1])
                elif action == "create_file":
                    response = self.file_interaction.create_file(params[1], "")
                elif action == "write_to_file":
                    response = self.file_interaction.write_to_file(params[1], params[2])
                elif action == "search_files":
                    response = self.file_interaction.search_files(params[1])
                elif action == "delete_file":
                    response = self.file_interaction.delete_file(params[1])
                else:
                    response = "Command not recognized."
            except Exception as e:
                response = str(e)

            return response
        else:
            return None
