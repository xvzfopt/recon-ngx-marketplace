# =====================================================================================
# Imports: External
# =====================================================================================
import os
import sys
import json
import yaml
from datetime import datetime
from copy import deepcopy
from pathlib import Path

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.utils import utils

# =====================================================================================
# Functions
# =====================================================================================
def output(line, error=False):
    '''
    Prints an output line to the console

    :param line: The string/line to be printed
    :type line: str
    '''
    marker = "[+]"
    if error:
        marker = "[!]"
    print(f"{marker} {line}")

def get_current_index():
    '''
    Loads and returns the data in existing Modules index YAML file

    :returns: The module inventory from the existing modules.yml file
    :rtype: dict
    '''
    with open('modules.yml') as index_file:
        index = yaml.safe_load(index_file)
    return index

def build_index():
    '''
    Builds an Index of the current Module inventory

    :returns: Index of current Module inventory
    :rtype: dict
    '''
    module_paths = find_modules()
    modules = []
    base_modules_path = os.path.join(Path(__file__).parent)

    # =====================================================================================
    # Process meta of discovered Modules
    # =====================================================================================
    for module_path in sorted(module_paths):
        fqn = os.path.split(module_path)[0]
        module_data = {}
        module_name = fqn.split("/")[-1]
        module_file_path = os.path.join(base_modules_path, module_path)

        # Attempt Module load
        try:
            module = utils.load_file_module(module_name, module_file_path)
        except ImportError:
            output("Skipping broken or unsupported module: %s" % module_name, True)
            continue

        # Process Meta
        module_meta = module.Module.meta
        module_data["name"]             = module_meta.name
        module_data["path"]             = fqn
        module_data["author"]           = module_meta.author
        module_data["description"]      = module_meta.description
        module_data["version"]          = module_meta.version
        module_data["dependencies"]     = module_meta.dependencies
        module_data["files"]            = module_meta.files
        module_data["required_keys"]    = module_meta.required_keys
        modules.append(module_data)
        output("Metadata built for module: %s " % module_name)

    return modules

def find_modules():
    '''
    Crawls the modules directory and finds modules

    :returns: List of found modules as file paths
    :rtype: list
    '''
    modules = []

    # Walk modules directory
    for dirpath, dirnames, filenames in os.walk('modules', followlinks=True):
        # Ignore hidden files and directories
        filenames = [f for f in filenames if not f[0] == '.']
        dirnames[:] = [d for d in dirnames if not d[0] == '.']
        if len(filenames) > 0:
            # Ignore non-python files
            for filename in [f for f in filenames if f.endswith('.py')]:
                modules.append(os.path.join(dirpath, filename))

    return modules

def save_index(index_data, dest):
    '''
    Saves the Index data to disk

    :param index_data: The Index data to be saved
    :type index_data: dict
    :param dest: The destination file path
    :type dest: str
    '''
    with open(dest, 'w') as index_file:
        yml = yaml.safe_dump(index_data)
        index_file.write(yml)

def json_print(data):
    '''
    Helper/Debug method to pretty print data as JSON

    :param data: The JSON-compatible data to be printed
    :type data: any
    '''
    print(json.dumps(data, indent=2))

def merge_modules_index(existing_index, new_index, key='path'):
    '''
    Merges the existing and new module indexes together

    :param existing_index: The existing module index, loaded from the existing modules.yml file
    :type existing_index: dict
    :param new_index: The new module index created from the current module inventory
    :type new_index: dict
    '''
    merged_index = []

    # Iterate new index modules
    for new_entry in new_index:
        # Check if new entry is present in existing index
        for existing_entry in existing_index:
            if new_entry["path"] == existing_entry["path"]:
                new_entry['last_updated'] = existing_entry.get('last_updated')

                # Check if Module has been updated
                if new_entry != existing_entry:
                    output(f"Changes detected in {existing_entry[key]}.")
                    new_entry['last_updated'] = datetime.strftime(datetime.now(), '%Y-%m-%d')

                # Overlay new entry data onto existing, then add to merged index
                merged_index.append({**existing_entry, **new_entry})
                break

    return merged_index

# =====================================================================================
# MAIN
# =====================================================================================
if __name__ == "__main__":
    # Load existing Modules YAML
    output("Loading existing modules.yml")
    current_index = get_current_index()

    # Build Index from current Modules
    output("Building module index")
    modules = build_index()

    # Merge Indexes
    output("Merging module indexes")
    new_index = merge_modules_index(current_index, modules)

    # Write Module Index to disk
    output("Saving new index")
    save_index(new_index, "modules.yml")

    output("Module Index Complete.")
    output(f"{len(modules)} module(s) indexed.")
