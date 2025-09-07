import traceback
import importlib.util
from glob import glob
from pathlib import Path
from pprint import pprint
from inspect import isabstract
import os, textwrap, sys, types
from importlib.abc import Loader
from collections import defaultdict

root_folder: str = os.path.dirname(os.path.abspath(__file__))
root_folder_name: str = os.path.basename(root_folder)

def get_all_subclasses(cls):
    subclasses = {}
    for subclass in cls.__subclasses__():
        subclasses[subclass.__name__] = subclass
        subclasses.update(get_all_subclasses(subclass))
    return subclasses

def get_ext_project_folder() -> str:
    """
    Returns the path to the external project folder.
    """

    # get parent directory of the current file
    current_dir = os.path.abspath(os.path.dirname(__file__))
    parent_dir = os.path.dirname(current_dir)

    # find all subfolders of parent_dir except this one
    subfolders = [f.path for f in os.scandir(parent_dir) if f.is_dir() and f.path != current_dir]
    # check which subfolder has a .git repo
    for folder in subfolders:
        if os.path.exists(os.path.join(folder, '.git')):
            break
    else:
        assert False, "No external project folder found. Did you set up your folder structure as seen in class?"

    return folder

def get_subclasses_from_file(filepath, base_classes, package_root):
    """
    Given the filepath to a Python source file, this function dynamically loads the module,
    then returns a dictionary for the classes defined in that module which inherit from the given classname.
    """

    def ensure_package_registered(package_name: str, package_root: str):
        if package_name not in sys.modules:
            pkg = types.ModuleType(package_name)
            pkg.__path__ = [package_root]
            sys.modules[package_name] = pkg

    package_root_folder = os.path.basename(package_root)

    ensure_package_registered(package_root_folder, package_root)

    rel_path = os.path.relpath(filepath, package_root)
    module_name = os.path.splitext(rel_path)[0].replace(os.sep, ".")
    
    full_module_name = package_root_folder + "." + module_name
    #print("Loading module", full_module_name, f"({package_root_folder}, {module_name}) from", filepath)

    spec = importlib.util.spec_from_file_location(
        full_module_name, filepath,
        submodule_search_locations=[os.path.dirname(filepath)]
    )
    assert spec, f"Could not load spec for {filepath}"
    
    module = importlib.util.module_from_spec(spec)    
    module.__package__ = full_module_name.rpartition('.')[0]

    try:
        assert isinstance(spec.loader, Loader)
        spec.loader.exec_module(module)
    except:
        print("Error loading module", full_module_name, "from", filepath)
        print("Error traceback:", traceback.format_exc())
        raise Exception(f"Error loading module {full_module_name} from {filepath}. Please check the error traceback above.")
    print("Loaded module", full_module_name, "from", filepath)

    subclasses = defaultdict(dict)
    for name in dir(module):
        obj = getattr(module, name)
        for base_class in base_classes:
            #if isinstance(obj, type) and any("Map" in base.__name__ or "MapObject" not in base.__name__ for base in obj.__bases__):
            #    print("Found class", name, "in", filepath)
            #    print("  Inherits from", obj.__bases__)
            #    print("  Is subclass of", base_class, ":", issubclass(obj, base_class))
            #    print("  Is not base class:", obj is not base_class)
            #    #if "example" in name.lower():
            #    #    input()
            if isinstance(obj, type) and issubclass(obj, base_class) and obj is not base_class and not isabstract(obj):
                subclasses[base_class][name] = obj
    return subclasses

def get_default_search_paths():
    search_paths = [
        (root_folder_name, f'{root_folder_name}/maps/ext/'),
        (root_folder_name, f'{root_folder_name}/maps/'),
    ]

    ext_folder = None
    if not any("server_remote" in arg for arg in sys.argv) and not any("editor" in arg for arg in sys.argv):
        ext_folder = get_ext_project_folder()
        search_paths.append((ext_folder, f'{ext_folder}/'))
    
    return search_paths

def get_subclasses_from_folders(base_classes, verbose=True, search_paths=None, ignore_classes={}) -> dict:
    print("Getting subclasses from folders...")
    #pprint(traceback.format_stack())
    if search_paths is None:
        search_paths = get_default_search_paths()

    classes = {}
    ext_folder = None
    if not any("server_remote" in arg for arg in sys.argv) and not any("editor" in arg for arg in sys.argv):
        ext_folder = get_ext_project_folder()
    all_files = set()
    for project_root, filepath in search_paths:
        if project_root == ext_folder:
            files = [
                os.path.join(path, file) 
                for path, _, files in os.walk(project_root)
                if ".venv" not in path and "site-packages" not in path
                for file in files 
                if file.endswith(".py")
            ]
        else:
            files = glob(os.path.join(filepath, "*.py"))
        
        if verbose: print(project_root, filepath, files)

        all_found_classes_for_path = {}
        for file in files:
            if file in all_files or 'imports' in file or Path(file).stem.startswith('test'):
                continue
            found_classes = get_subclasses_from_file(file, base_classes, project_root)
            check_for_conflicts(found_classes, classes)
            for base_class, classes_ in found_classes.items():
                if base_class not in all_found_classes_for_path:
                    all_found_classes_for_path[base_class] = {}
                for class_ in classes_:
                    if class_ in ignore_classes.get(base_class, []):
                        #print("Ignoring class", class_, "in", file)
                        continue
                    all_found_classes_for_path[base_class][class_] = classes_[class_]
                #all_found_classes_for_path[base_class].update(classes_)
        all_files.update(files)

        for base_class, classes_ in all_found_classes_for_path.items():
            if base_class not in classes:
                classes[base_class] = {}

            classes[base_class].update(classes_)
            if verbose: print("Found", len(classes_), "subclasses of", base_class, "in", file)

    for base_class, classes_ in classes.items():
        if verbose: print("Found", len(classes_), "subclasses of", base_class)
        #assert len(classes_) > 0

        for name, cls in classes_.items():
            if verbose: print("  ", name, "->", cls)

    print("All files:", all_files)
    return classes

def check_for_conflicts(classes, existing_classes):
    # check for conflicts between classes in provided dict and current namespace
    for base_class, classes_ in classes.items():
        for name, cls in classes_.items():
            #print("Checking for conflicts with", base_class, name)
            if name in existing_classes.get(base_class, {}) and existing_classes[base_class][name] is not cls:
                print(name, cls, existing_classes[base_class][name])
                raise Exception(f"Class {name} already exists in namespace. Please do not create your own class with the same name as that.")

def shorten_lines(lines, max_length):
    short_lines = []
    for line in lines:
        if len(line) > max_length:
            short_lines.extend(textwrap.fill(line, max_length).split('\n'))
        else:
            short_lines.append(line)
    return short_lines

def get_valid_emails():
    if not os.path.exists('emails.csv'):
        return []

    valid_emails = set()
    with open('emails.csv') as f:
        for line in f:
            valid_emails.add(line.strip())
    return valid_emails
