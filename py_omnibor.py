#
# Author: Robert Marion
#
import inspect
import os
import importlib.util
import hashlib
import argparse

GITOID_PREFIX = "gitoid:blob:sha1:"
OUT_FILE_NAME = "OmniBor.sha1"


def get_imported_modules(entry_point):
    module_to_write = set()
    imported_modules = set()

    # Get the entry point module
    spec = importlib.util.spec_from_file_location("__main__", entry_point)
    importlib.invalidate_caches()
    entry_point_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry_point_module)

    # Traverse the module hierarchy and find all imported modules
    modules_to_process = [entry_point_module]
    while modules_to_process:
        module = modules_to_process.pop()
        module_name = module.__name__
        if module_name not in imported_modules:
            imported_modules.add(module_name)
            try:
                file_path = inspect.getfile(module)
                if file_path.endswith('.py') or file_path.endswith('.pyd') or file_path.endswith('.pyo'):
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        hash_object = hashlib.sha1(content)
                        hex_dig = hash_object.hexdigest()
                        module_name += f' ({GITOID_PREFIX}{os.path.basename(file_path)}:{hex_dig})'
            except Exception:
                pass
            try:    
                for name, obj in inspect.getmembers(module):
                    if inspect.ismodule(obj):
                        if obj.__name__.startswith('builtins'):
                            continue
                        modules_to_process.append(obj)
                        module_to_write.add(f' {GITOID_PREFIX}{os.path.basename(file_path)}:{hex_dig}')
                    elif file_path.endswith('.pyd') or file_path.endswith('.pyo'):
                        module_to_write.add(f' {GITOID_PREFIX}{os.path.basename(file_path)}:{hex_dig}')
            except Exception:
                print("WARNING: A library may need to be pip installed")                
    return module_to_write


def write_manifest(deps):
    try:
        with open(OUT_FILE_NAME, "w") as f:
            set_string = '\n'.join(str(element) for element in deps)
            f.write(set_string)
    except:
        print(f"Could not open {OUT_FILE_NAME}")

def experiment_write_to_pyc(deps, target_file):
    '''This will write directly to the .pyc file.
    Writing to the pyc file seems to not damage the file
    but it is probably a bad practice as there is no guarantee 
    this will work in all releases or future releases of python'''
    subdirectory = './__pycache__'
    if not os.path.exists(subdirectory):
        print("Cannot write to pyc file because it is not found")
        return
        
    for file in os.listdir(subdirectory):
        file_prefix = os.path.splitext(target_file)[0]
        if file.startswith(file_prefix) and file.endswith('.pyc'):
            file_path = os.path.join(subdirectory, file)
            print("File found at:", file_path)
            with open(file_path, 'a') as file:
                file.write("BEGIN OMNIBOR\n")
                file.write(deps)
                file.write("\nEND OMNIBOR")
            break
    else:
        print("File not found.")


def main():
    parser = argparse.ArgumentParser(description='Retrieve imported modules with file paths and SHA1 hashes.')
    parser.add_argument('--append-manifest', action='store_true', help='Optional flag to append manifest')
    parser.add_argument('entry_point', type=str, help='The path to the entry point Python file.')
    args = parser.parse_args()

    modules = get_imported_modules(args.entry_point)
    write_manifest(modules)
    if args.append_manifest:
        experiment_write_to_pyc(str(modules), args.entry_point)
    print(f"Done. Check {OUT_FILE_NAME} for output")


if __name__ == '__main__':
    main()
