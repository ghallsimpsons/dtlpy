from m2r import parse_from_file, save_to_file
from urllib.request import urlretrieve
import os
import json

LOCAL = None  # or path to local doc repo
"""
Image annotations: setup

    MD to RST mapping
    # : ====
    ## : --------
    ### : ^^^^
    #### : ~~~~~~~~~
    ##### : ""

    """
# LEVELS = ['-', '~', '~', '<', '@']
LEVELS = ['-', '*', '^']
HMARKS = {1: '"',
          2: '"',
          3: '"',
          4: '~',
          5: '~',
          }


def get_file(filepath):
    try:
        if LOCAL is not None:
            filepath = os.path.join(LOCAL, filepath)
        else:
            print('getting: {}'.format(filepath))
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            urlretrieve(
                url="https://raw.githubusercontent.com/dataloop-ai/dtlpy-documentation/main/{}".format(filepath),
                filename=filepath)
    except Exception:
        print('Failed getting: {}'.format(filepath))
    return filepath


def extract_index_rec(root, filename, rst_string, level):
    filepath = root + '/' + filename
    filepath = get_file(filepath)
    with open(filepath) as f:
        index = json.load(f)
    for content in index['content']:
        name, ext = os.path.splitext(content['location'])

        if ext == '.json':
            rst_string += '\n'
            rst_string += '{}\n'.format(LEVELS[level] * len(content['displayName']))
            rst_string += '{}\n'.format(content['displayName'])
            rst_string += '{}\n'.format(LEVELS[level] * len(content['displayName']))
            rst_string += '{}\n'.format(content['description'])
            rst_string += '\n'
            rst_string += '.. toctree::\n'
            # rst_string += '   :numbered: \n'
            rst_string += '   :caption: {}\n'.format(content['displayName'])
            rst_string += '   :maxdepth: 6\n'
            rst_string += '   :hidden:\n'
            rst_string += '\n'
            rst_string = extract_index_rec(root=root,
                                           filename=content['location'],
                                           rst_string=rst_string,
                                           level=level + 1)
        else:
            rst_string += '\n'
            filepath = root + '/' + content['location']
            get_file(filepath=filepath)

            from m2r import RestRenderer, M2R
            renderer = RestRenderer()
            renderer.hmarks = HMARKS
            with open(filepath, encoding='utf-8') as f:
                src = f.read()
            output = M2R(renderer=renderer)(src)

            # output = parse_from_file(filepath)
            rst_filepath = filepath.replace('.md', '.rst')
            rst_filepath = os.path.dirname(rst_filepath) + '.rst'
            if os.path.isfile(rst_filepath):
                os.remove(rst_filepath)

            # save_to_file(rst_filepath, output)
            # os.remove(filepath)
            # rst_string += '{}\n'.format(LEVELS[level] * len(content['displayName']))
            # rst_string += '{}\n'.format(content['displayName'])
            # rst_string += '{}\n'.format(LEVELS[level] * len(content['displayName']))
            # rst_string += '\n'
            # rst_string += '{}\n'.format(content['description'])
            # rst_string += '\n'
            rst_string += '   {}\n'.format(filepath)
            # rst_string += '  :parser: #myst_parser.sphinx_\n'
            # rst_string += '\n'
    return rst_string


def main():
    root = 'tutorials'
    filename = 'index.json'
    rst_string = ''
    rst_string += '{}\n'.format('Tutorials')
    rst_string += '{}\n'.format('=========')
    rst_string += '\n'
    rst_string = extract_index_rec(root=root,
                                   filename=filename,
                                   rst_string=rst_string,
                                   level=0)
    with open('tutorials.rst', 'w') as f:
        f.write(rst_string)


if __name__ == "__main__":
    main()
