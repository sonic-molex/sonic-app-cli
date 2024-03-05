import sys
import libyang as ly
from typing import Optional
import datetime


debug_enable = True
title_src = 'openconfig'
title_dest = 'sonic'


class Annotation:
    """
    Parse annotation yang file
    """

    def __init__(self, search_path, yang_file) -> None:
        self.search_path = search_path
        self.yang_file = yang_file
        self.info = {}
        self.tables = []
        self.fields = []
        self.keys = []
        self.__config = []
        self.parse()


    def leaf_value(self, content, key) -> Optional[str]:
        pos = content.find(key)
        if pos != -1:
            pos1 = content.find('"', pos) + 1
            pos2 = content.find('"', pos1)
            return content[pos1:pos2].strip()
        
        return None


    def key_xpath(self, deviation, key) -> Optional[list]:
        field_name = self.leaf_value(deviation, key)
        if field_name is None:
            return None
        
        xpath = deviation[:deviation.find('{')].strip()[1:-1]

        # if namespace needed, use xpath.replace(self.info['src_module'][1], self.info['src_module'][0])
        xpath = xpath.replace(self.info['src_module'][1] + ':', '')

        return [xpath, field_name]


    def table_name(self, deviation) -> None:
        table_name = self.leaf_value(deviation, 'sonic-ext:table-name')
        if table_name is None:
            return
        
        xpath = self.key_xpath(deviation, 'sonic-ext:table-name')[0]

        db_name = self.leaf_value(deviation, 'sonic-ext:db-name')
        if db_name is None or db_name == 'CONFIG_DB':
            self.__config.append('config')
            self.tables.append([xpath, table_name, table_name, self.__config[-1], 'CONFIG-DB', True])
        elif db_name == 'STATE_DB':
            self.__config.append('state')
            self.tables.append([xpath, table_name, table_name + '_STATE', self.__config[-1], db_name, False])
        else:
            raise Exception("Not support the db name " + db_name)

        self.fields.append([])

        return


    def field_name(self, deviation) -> None:
        v = self.key_xpath(deviation, 'sonic-ext:field-name')
        if v is None:
            return


        for i in range(len(self.tables)):
            if v[0].find(self.tables[i][0]) != -1 and v[0].find('/' + self.tables[i][3] + '/') != -1:
                self.fields[i].append(v)
                break


    def key_name(self, deviation) -> None:
        v = self.key_xpath(deviation, 'sonic-ext:key-transformer')
        if v is None:
            return

        if v[0][(v[0].rfind('/') + 1):] not in self.__config:
            v[0] += '/config'

        self.keys.append(v[0])


    def parse(self) -> None:
        """
        Examples for arguments:
        info: list, eg. {'src_module': [yang module name, yang module prefix], 'imports': [[yang module name, yang module prefix], ...]}
        tables: array, eg. [[xpath, table name, db name, config mark, config boolean], ...]
        fields: array, eg. [[[xpath, field name], ...], ...]
        keys: array, eg. [xpath, ...]
        """
        imports = []
        ctx = ly.Context(self.search_path, leafref_extended=True)
        module = ctx.load_module(self.yang_file)
        for imp in module.imports():
            if imp.name().find(title_src) != -1:
                self.info['src_module'] = [imp.name(), imp.prefix()]
            else:
                imports.append([imp.name(), imp.prefix()])
        self.info['imports'] = imports

        debug_print(self.info)

        content = module.print('yang', ly.IOType.MEMORY)
        deviations = content.split(' deviation ')
        for deviation in deviations[1:]:
            deviation = deviation.strip()
            self.table_name(deviation)
            self.field_name(deviation)
            self.key_name(deviation)

        debug_print(self.tables)
        debug_print(self.fields)
        debug_print(self.keys)


class Generator:
    """
    Generate sonic yang file by annotation and open-config yang files.
    """

    def __init__(self, search_path, annot) -> None:
        self.search_path = search_path
        self.annot = annot
        self.ctx = ly.Context(search_path, leafref_extended=True)
        self.module = self.ctx.load_module(annot.info['src_module'][0])
        self.module_name = self.__name()

    
    def __name(self) -> str:
        name = self.module.name()
        if name.find(title_src) == -1:
            raise Exception("Failed to tranform module name. Invalid tranform key: " + title_src)

        return name.replace(title_src, title_dest)


    def __to_words(self, xpath) -> str:
        xpath = xpath.replace(self.module.name() + ':', '')
        return xpath[1:xpath.find('/', 1)].replace('-', ' ')


    def namespace(self) -> str:
        return 'namespace "http://github.com/Azure/' + self.module_name + '";'


    def prefix(self, title) -> str:
        prefix = 'prefix '
        words = self.module_name.split('-')

        for wd in words:
            if wd == title:
                prefix += wd
            else:
                prefix += '-'
                prefix += wd[:3]

        prefix += ';'

        return prefix


    def imports(self) -> str:
        return 'import sonic-extension { prefix sonic-ext; }'


    def organization(self) -> str:
        return 'organization "SONiC";'


    def contact(self) -> str:
        return 'contact "SONiC";'


    def description(self) -> str:
        return 'description "' + self.module.description() + '";'


    def revision(self) -> str:
        return 'revision ' + datetime.date.today().strftime('%Y-%m-%d') + '{ description "Initial revision.";}'


    def gen_type(self, node) -> str:
        text = 'type '

        type = node.type()
        if type.base() in ly.Type.STR_TYPES:
            text += ly.Type.BASENAMES[ly.Type.STRING]
        elif type.leafref_type() is not None:
            text += type.leafref_type().basename()
        else:
            text += type.basename()

        fraction_digits = type.fraction_digits()
        if fraction_digits is None:
            text += ';'
        else:
            text += '{fraction-digits ' + str(fraction_digits) + ';}'

        return text


    def gen_unit(self, node) -> str:
        text = ''

        if hasattr(node, 'units') and node.units() is not None:
            text += 'units ' + node.units() + ';'

        return text


    def gen_leaf(self, xpath, key) -> str:
        debug_print('leaf xpath: ' + xpath)

        node = next(self.ctx.find_path(xpath))
 
        # leaf name
        text = 'leaf ' + (node.name() if key is None else key) + ' {'
        # leaf description
        text += 'description "' + node.description() + '";'
        # leaf basic type
        text += self.gen_type(node)
        # leaf units
        text += self.gen_unit(node)

        text += '}'

        return text


    def gen_list(self, index) -> str:
        xpath = self.annot.keys[index]
        debug_print(xpath)

        node = next(self.ctx.find_path(xpath))
        text = ''

        if any(node.parent().keys()) :
            name = next(node.parent().keys()).name()
            text += 'key "' + name + '";'

            # The key leaf
            #key_path = self.annot.fields[index][0][0]
            #key_path = key_path[:(len(key_path) - len(self.annot.fields[index][0][1]))] + name
            key_path = next(node.children()).schema_path()
            debug_print(key_path)
            text += self.gen_leaf(key_path, name)

        for field in self.annot.fields[index]:
            text += self.gen_leaf(field[0], field[1])

        return text


    def gen_container(self, index) -> str:
        name = self.__to_words(self.annot.keys[index])
        text = 'container ' + self.annot.tables[index][2] + ' {'
        # config
        if self.annot.tables[index][3]:
            text += 'description "Configuration data for ' + name + 's in ' + self.annot.tables[index][4] + '.";'
        # state
        else:
            text += 'config false;sonic-ext:db-name "' + self.annot.tables[index][4] + '";description Operational state data for ' + name + 's in ' + self.annot.tables[index][4] + '.";'

        text += 'list ' + self.annot.tables[index][1] + '_LIST {'

        text += self.gen_list(index)

        text += '}}'

        return text


    def gen_head(self) -> str:
        text = 'module ' + self.module_name + ' {'
        text += self.namespace()
        text += self.prefix(title_dest)
        text += self.imports()
        text += self.organization()
        text += self.contact()
        text += self.description()
        text += self.revision()
        text += 'container ' + self.module_name + '{'

        return text
    

    def gen_tables(self) -> str:
        text = ''

        for i in range(len(self.annot.keys)):
            text += self.gen_container(i)

        text += '}}'

        return text
    

    def gen_yang(self) -> str:
        text = self.gen_head()
        text += self.gen_tables()

        debug_print(text)
        return text
    

    def to_file(self, yang, out_dir) -> str:
        ctx = ly.Context(self.search_path)
        module = ctx.parse_module_str(yang)
        text = module.print("yang", ly.IOType.MEMORY)

        debug_print(text)

        path = out_dir.strip()
        if path[-1] != '/':
            path += '/'
        path += self.module_name + '.yang'

        with open(path, 'w') as f:
            f.write(text)

        return path


def debug_print(data):
    if debug_enable:
        print(data)


def sonic_yanggen(search_path, annot_module_name, out_dir) -> Optional[str]:
    try:
        # 1. parse the annotation yang file
        annot = Annotation(search_path, annot_module_name)

        # 2. create yang text by source module
        gen = Generator(search_path, annot)
        text = gen.gen_yang()

        # 3. format yang text and output file
        path = gen.to_file(text, out_dir)

        print('Generated', path)

        # return module name and yang text content for extension
        return {'name': gen.module_name, 'yang': text.replace('\n', '')}
        
    except Exception as e:
        print(e)

    return None


def main(argv):
    """
    argv[1]: yang model search directory
    argv[2]: annotation yang file path
    argv[3]: output directory for generation file
    """

    sonic_yanggen(argv[1], argv[2], argv[3])

    # examples
    #sonic_yanggen('/home/sonic/work/oplinklum/openconfig', 'openconfig-optical-attenuator-annot', '/home/sonic/work/test')
    #sonic_yanggen('/home/sonic/sonic/sonic-ot-extension/src/sonic-mgmt-common/models/yang', 'openconfig-optical-attenuator-annot', '/home/sonic/work/test')
    #sonic_yanggen('/home/sonic/sonic/sonic-buildimage/src/sonic-mgmt-common/models', 'openconfig-optical-amplifier-annot', '/home/sonic/work/test')


if __name__ == "__main__":
    main(sys.argv)
