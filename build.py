import os
import sys
from jinja2 import Template, FileSystemLoader, Environment
sys.path.append('./')
from sonic_yanggen import sonic_yanggen, ANNOTATION_SUFFIX, YANG_SUFFIX


def parse_config(config_file):
    """
    Parse the config file
    """
    yang_dir = ''
    yang_imps = []
    yang_annots = []

    with open(config_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()

            if len(line) == 0 or line[0] == '#':
                continue

            if line[0] == '/':
                yang_dir = line
                continue

            if YANG_SUFFIX not in line:
                continue

            module = line.replace(YANG_SUFFIX, '')

            if module[-len(ANNOTATION_SUFFIX):] == ANNOTATION_SUFFIX:
                yang_annots.append(module)
            else:
                yang_imps.append(module)

    # to support both sonic yang and sonic annots yang files.
    #if len(yang_imps) != len(yang_annots):
    #    raise Exception('Invalid config. The number of annotations is inconsistent with the number to be converted.')

    return [yang_dir, yang_imps, yang_annots]


def main(argv):
    """
    argv[1]: container version
    argv[2]: container name
    """

    #parse config file
    cfg = parse_config('./config')

    yang_dir_in = cfg[0] + '/models/yang'
    yang_dir_out = './yang'
    if not os.path.exists(yang_dir_out):
        os.mkdir(yang_dir_out)

    #automatically generate annotation yang to sonic yang
    modules = []
    for mod in cfg[1]:
        name = mod
        for annot in cfg[2]:
            if name + ANNOTATION_SUFFIX == annot:
                name = annot
                break
        data = sonic_yanggen(yang_dir_in, name, yang_dir_out)
        modules.append(data)

    #j2 manifest
    j2_loader = FileSystemLoader('./')
    env = Environment(loader = j2_loader)

    j2_template = env.get_template('./manifest.json.j2')
    j2_modules = '"'
    for module in cfg[1]:
        j2_modules += module
        j2_modules += '", "'

    j2_modules = j2_modules[:-3]
    j2_manifest = j2_template.render(version = argv[1], container_name = argv[2], config_modules = j2_modules, show_modules = j2_modules)
    j2_manifest = j2_manifest.replace('\n', '')

    #j2 docker file
    j2_template = env.get_template('./Dockerfile.j2')
    j2_out = j2_template.render(manifest = j2_manifest, modules = modules)

    with open('./Dockerfile', 'w') as f:
        f.write(j2_out)

    print('Generate docker file completed.')


if __name__ == "__main__":
    main(sys.argv)