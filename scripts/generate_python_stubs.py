import os
import tomllib

OUTPUT_DIR = 'python_stubs'

def sanitize(name: str) -> str:
    return name.replace('/', '_').replace('-', '_')

def main():
    with open('Cargo.toml', 'rb') as f:
        cargo = tomllib.load(f)
    members = cargo['workspace']['members']
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for member in members:
        pkg_name = sanitize(member)
        pkg_path = os.path.join(OUTPUT_DIR, pkg_name)
        os.makedirs(pkg_path, exist_ok=True)
        init_file = os.path.join(pkg_path, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as fh:
                fh.write(f'"""Python stub for crate `{member}`."""\n\n')
                fh.write('class Placeholder:\n    pass\n')
    print(f'Generated {len(members)} stubs in {OUTPUT_DIR}/')

if __name__ == '__main__':
    main()
