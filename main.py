import json

from generator import ArtefactsGenerator


def main() -> None:
    """
    Execution of config and meta generation.
    """

    with open('input/test_input.xml', 'r', encoding='utf-8') as f:
        input_data = f.read()

    gen = ArtefactsGenerator(input_data)
    gen.pipeline()

    with open('out/config.xml', 'w', encoding='utf-8') as f:
        f.write(gen.config)

    with open('out/meta.json', 'w', encoding='utf-8') as f:
        json.dump(gen.meta, f, indent=4)


if __name__ == '__main__':
    main()
