import json
from FileSystemInteraction import JarvisFileInteraction

class JarvisAssistant:
    def __init__(self, exe_paths=None):
        self.file_interaction = JarvisFileInteraction(exe_paths=exe_paths)

    def classify_intent(self, command: str):
        """
        Use the LLM to parse the user command into an action and parameters.
        Valid actions: open_directory, search_files, delete_file, open_file,
        execute_app, get_time, get_weather, or NONE.
        Returns a tuple (action, params_list).
        """
        # defer import to avoid circular dependency
        from main import llm

        system_prompt = {
            "role": "system",
            "content": (
                "You are a command parser. Given a user instruction, "
                "identify the best matching action and its arguments. "
                "Valid actions: open_directory, search_files, delete_file, open_file, execute_app, get_time, get_weather, NONE. "
                "Respond with JSON like:{\"action\":ACTION,\"params\":[LIST]}. "
                "If none match, use action NONE and empty params."
            )
        }
        user_prompt = {"role": "user", "content": command}
        try:
            response = llm.create_chat_completion(
                messages=[system_prompt, user_prompt],
                temperature=0
            )
            content = response["choices"][0]["message"]["content"]
            data = json.loads(content)
            action = data.get("action")
            params = data.get("params", [])
        except Exception:
            action, params = None, []
        return action, params

    def parse_command(self, command: str):
        """Parse user command via LLM-based intent classification."""
        return self.classify_intent(command)

    def execute_command(self, command: str):
        """
        Execute parsed command by dispatching to FileSystemInteraction or other actions.
        """
        action, params = self.parse_command(command)
        print(f"ACTION>>>>>> {action}")
        print(f"PARAMS>>>>>> {params}")
        print(f"COMMAND>>>>>> {command}")

        if not action or action == "NONE":
            return None

        try:
            if action == "open_directory":
                return self.file_interaction.open_directory(params[0])
            elif action == "search_files":
                return self.file_interaction.search_files(params[0])
            elif action == "delete_file":
                return self.file_interaction.delete_file(params[0])
            elif action == "open_file":
                return self.file_interaction.open_file(params[0])
            elif action == "execute_app":
                return self.file_interaction.execute_app(params[0])
            elif action == "get_time":
                return self.file_interaction.get_time()
            elif action == "get_weather":
                return self.file_interaction.get_weather()
            else:
                return "Command not recognized."
        except Exception as e:
            return str(e)
