import fnmatch
import os
from functools import cmp_to_key

from mkdocs.utils import MARKDOWN_EXTENSIONS


class Files(object):
    def __init__(self, files):
        self._files = files
        self.input_paths = {file.input_path: file for file in files}

    def __iter__(self):
        return iter(self._files)

    def __len__(self):
        return len(self._files)

    def documentation_pages(self):
        return [file for file in self if file.is_documentation_page()]

    def static_pages(self):
        return [file for file in self if file.is_static_page()]

    def media_files(self):
        return [file for file in self if file.is_media_file()]

    def javascript_files(self):
        return [file for file in self if file.is_javascript()]

    def css_files(self):
        return [file for file in self if file.is_css()]


class File(object):
    def __init__(self, from_dir, path, filename=None):
        # The filename may already been parsed out of the path,
        # but if not then determine it now.
        if filename is None:
            filename = os.path.basename(path)

        root, extension = os.path.splitext(filename)
        self.root = root  # The filename, without any extension.
        self.extension = extension.lower()

        self.input_path = path
        self.full_input_path = os.path.normpath(os.path.join(from_dir, self.input_path))
        self.output_path = self.get_output_path()

    def get_output_path(self):
        """
        Map input source documents to the output build file.
        """
        if self.is_documentation_page():
            if self.root in ('index', 'README'):
                directory = os.path.dirname(self.input_path)
            else:
                directory = os.path.splitext(self.input_path)[0]
            return os.path.normpath(os.path.join(directory, 'index.html'))
        return os.path.normpath(self.input_path)

    def is_documentation_page(self):
        return self.extension in MARKDOWN_EXTENSIONS

    def is_static_page(self):
        return self.extension in (
            '.html',
            '.htm',
            '.xml',
            '.json',
        )

    def is_media_file(self):
        return not (self.is_documentation_page() or self.is_static_page())

    def is_javascript(self):
        return self.extension in (
            '.js',
            '.javascript',
        )

    def is_css(self):
        return self.extension in (
            '.css',
        )


def get_files(from_dir):
    files = []
    exclude = ['.*', '/templates']

    for (source_dir, dirnames, filenames) in os.walk(from_dir):
        relative_dir = os.path.relpath(source_dir, from_dir)

        for dirname in list(dirnames):
            path = os.path.normpath(os.path.join(relative_dir, dirname))
            # Skip any excluded directories
            if _filter_paths(basename=dirname, path=path, is_dir=True, exclude=exclude):
                dirnames.remove(dirname)
        dirnames.sort()

        for filename in sort_files(filenames):
            path = os.path.normpath(os.path.join(relative_dir, filename))
            # Skip any excluded files
            if _filter_paths(basename=filename, path=path, is_dir=False, exclude=exclude):
                continue
            file = File(from_dir, path, filename)
            files.append(file)

    return Files(files)


def sort_files(filenames):
    """
    Always sort index as first filename in list.
    """

    def compare(x, y):
        if x == y:
            return 0
        if os.path.splitext(y)[0] == 'index':
            return 1
        if  os.path.splitext(x)[0] == 'index' or x < y:
            return -1
        return 1

    return sorted(filenames, key=cmp_to_key(compare))


def _filter_paths(basename, path, is_dir, exclude):
    """
    .gitignore style file filtering.
    """
    for item in exclude:
        # Items ending in '/' apply only to directories.
        if item.endswith('/') and not is_dir:
            continue
        # Items starting with '/' apply to the whole path.
        # In any other cases just the basename is used.
        match = path if item.startswith('/') else basename
        if fnmatch.fnmatch(match, item.strip('/')):
            return True
    return False
