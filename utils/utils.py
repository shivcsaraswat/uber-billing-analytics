import yaml 


# Loads requested yaml file located at file_path
def load_config(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
    
    
    