import re


class ArtefactsGenerator:
    """
    Generates files with station's config and metadata of its classes.
    """
    def __init__(self, data: str):
        """
        Initialize an instance of ArtefactsGenerator.
        :param data: string with the content of the input XML-file
        """
        self._data = data

        self.config = str()
        self.meta = list()

        self._class_data = self.extract_class_data()
        self._aggregation_data = self.extract_aggregation_data()

    def extract_class_names(self) -> list[str]:
        """
        Extracts class names from an input XML file.
        :return: list with class names
        """
        return re.findall(r'<Class name="(\w+)"', self._data)

    def extract_class_data(self) -> list[str]:
        """
        Extracts data for each class from the XML file.
        :return: list with data for each class
        """
        return re.findall(r'<Class[^>]*>.*?</Class>', self._data, re.DOTALL)

    def extract_aggregation_data(self) -> list[str]:
        """
        Performs the same for aggregation information.
        :return: list with aggregation data
        """
        return re.findall(r'<Aggregation.*?/>', self._data)

    @staticmethod
    def describe_attributes(class_info: str) -> list[dict]:
        """
        Describes attributes of a class, if given.
        :param class_info: string with info of a class
        :return: list of dicts with attributes' info or empty list
        """
        attrs = re.findall(r'<Attribute.*?/>', class_info)
        if not attrs:
            return []
        return [dict(re.findall(r'(\w+)="(\w+)"', i)) for i in attrs]

    def build_meta(self) -> list[dict]:
        """
        Builds the meta file with metadata of all classes.
        :return: list of dicts with classes' metadata
        """
        meta = []

        for i in self._class_data:

            info = dict()

            class_str = re.search(r'<Class[^>]+>', i).group()

            info['class'] = re.search(r'name="(\w+)"', class_str).group(1)
            info.update(dict(re.findall(r'(\w+)="([^"]+)"', class_str.strip('<Class name='))))
            info['isRoot'] = True if info['isRoot'] == 'true' else False

            try:
                aggregation = [i for i in self._aggregation_data if f'source="{info["class"]}"' in i][0]
                role = 'source'
            except IndexError:
                aggregation = [i for i in self._aggregation_data if f'target="{info["class"]}"' in i][0]
                role = 'target'
            mult = re.search(role + r'Multiplicity="([.\d]+)"', aggregation).group(1)
            minmax = tuple(mult.split('..')) if '..' in mult else (mult, mult)
            info.update(dict(zip(('min', 'max'), minmax)))

            info['parameters'] = self.describe_attributes(i)

            meta.append(info)

        return meta

    def find_sources(self, target: str) -> list[str]:
        """
        Finds sources by a target in aggregation relationships, if given.
        :param target: target class
        :return: list of its source classes or empty list
        """
        return [
            re.search(r'source="(\w+)"', i).group(1)
            for i in self._aggregation_data if f'target="{target}"' in i
        ]

    def build_block_for_class(self, name: str) -> list[str, list[str]]:
        """
        Builds an XML block with class tags and parameters tags. Recursive.
        :param name: name of the class
        :return: list with tags
        """
        block = [f'<{name}>', f'</{name}>']

        params = [i for i in self.meta if i['class'] == name][0]['parameters']
        if params:
            block.insert(-1, [f'<{i["name"]}>{i["type"]}</{i["name"]}>' for i in params])

        sources = self.find_sources(name)
        if not sources:
            return block
        for i in sources:
            block.insert(-1, self.build_block_for_class(i))

        return block

    def join_blocks(self, block: list, level: int = 0) -> str:
        """
        Joins blocks in a string, adding tabulation suitable for XML format. Recursive.
        :param block: XML block for a class, contains blocks of its source classes
        :param level: level of the block for tabulation
        :return: string with blocks suitable for XML format
        """
        return '\n'.join(
            '\t' * level + i if isinstance(i, str)
            else self.join_blocks(i, level + 1)
            for i in block
        )

    def build_config(self) -> str:
        """
        Builds a config XML file.
        :return: string with contents of the config
        """
        root = [i for i in self.meta if i['isRoot']][0]['class']
        config = self.build_block_for_class(root)
        return self.join_blocks(config)

    def pipeline(self) -> None:
        """
        Execution pipeline of a generator.
        """
        self.meta = self.build_meta()
        self.config = self.build_config()
