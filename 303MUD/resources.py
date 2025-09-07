
import os, sys
from pathlib import Path

from .util import get_ext_project_folder

root_folder = os.path.dirname(os.path.abspath(__file__))

def get_resource_path(resource_name: str = '', ext_folder=False) -> str:
    """ Returns the path to the resource with the given name. """
    if any("server_remote" in arg for arg in sys.argv):
        resource_name = resource_name.lower()
        ext_folder = False
    if not ext_folder:
        default_path = Path(f'{root_folder}/resources/{resource_name}')
        if default_path.exists():
            return str(default_path)
        if any("server_remote" in arg for arg in sys.argv):
            raise FileNotFoundError(f"Resource '{resource_name}' not found in {root_folder}/resources/")
    ext_project_path = get_ext_project_folder() + '/resources/' + resource_name
    ext_project_path = Path(ext_project_path).resolve()
    if ext_project_path.exists():
        return str(ext_project_path)
    raise FileNotFoundError(f"Resource '{resource_name}' not found in {root_folder}/resources/ or {ext_project_path}")

def find_resource_path(resource_name: str = '') -> Path:
    # recursively walk through resources directory and find first image with given filename
    resource_name = resource_name.lower()
    for root, dirs, files in os.walk(os.path.join(root_folder, 'resources')):
        for file in files:
            if file.lower() == resource_name + ".png":
                return Path(root) / file
    if not any("server_remote" in arg for arg in sys.argv):
        ext_project_path = get_ext_project_folder()
        for root, dirs, files in os.walk(os.path.join(ext_project_path, 'resources')):
            for file in files:
                print(f"Comparing {file.lower()} to = {resource_name + '.png'}")
                if file.lower() == resource_name + ".png":
                    print("FOUND")
                    return Path(root) / file

    raise FileNotFoundError(f"Resource '{resource_name}' not found in {root_folder}/resources/")

class Resources:
    def get_resource_path(self, resource_name: str, ext_folder=False) -> str:
        return get_resource_path(resource_name, ext_folder)