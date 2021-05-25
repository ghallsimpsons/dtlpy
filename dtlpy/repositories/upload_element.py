import os
import validators
from dtlpy import PlatformException, entities


class BaseUploadElement:

    def __init__(self, all_upload_elements: dict):
        self.upload_item_element = all_upload_elements['upload_item_element']
        self.total_size = all_upload_elements['total_size']
        self.remote_name = all_upload_elements['remote_name']
        self.remote_path = all_upload_elements['remote_path']
        self.upload_annotations_element = all_upload_elements['upload_annotations_element']
        self.item_metadata = all_upload_elements['item_metadata']
        self.with_head_folder = all_upload_elements['with_head_folder']
        self.file_types = all_upload_elements['file_types']
        self.type = None
        self.buffer = None
        self.remote_filepath = None
        self.exists_in_remote = False
        self.checked_in_remote = False
        self.annotations_filepath = all_upload_elements['annotations_filepath']
        self.link_dataset_id = None
        self.root = all_upload_elements['root']
        self.filename = all_upload_elements['filename']


class BinaryUploadElement(BaseUploadElement):

    def __init__(self, all_upload_elements: dict):
        super().__init__(all_upload_elements)

        # binary element
        if not hasattr(self.upload_item_element, "name") and self.remote_name is None:
            raise PlatformException(
                error="400",
                message='upload element type was bytes. Must put attribute "name" on buffer (with file name) '
                        'when uploading buffers or providing param "remote_name"')
        if self.remote_name is None:
            self.remote_name = self.upload_item_element.name
        remote_filepath = self.remote_path + self.remote_name
        self.type = 'buffer'
        self.buffer = self.upload_item_element
        self.remote_filepath = remote_filepath
        self.annotations_filepath = self.upload_annotations_element


class DirUploadElement(BaseUploadElement):

    def __init__(self, all_upload_elements: dict):
        super().__init__(all_upload_elements)

        _, ext = os.path.splitext(self.filename)
        if self.file_types is None or ext in self.file_types:
            filepath = os.path.join(self.root, self.filename)  # get full image filepath
            # extract item's size
            self.total_size += os.path.getsize(filepath)
            # get annotations file
            if self.upload_annotations_element is not None:
                # change path to annotations
                annotations_filepath = filepath.replace(self.upload_item_element,
                                                        self.upload_annotations_element)
                # remove image extension
                annotations_filepath, _ = os.path.splitext(annotations_filepath)
                # add json extension
                annotations_filepath += ".json"
            else:
                annotations_filepath = None
            if self.with_head_folder:
                remote_filepath = self.remote_path + os.path.relpath(filepath, os.path.dirname(
                    self.upload_item_element))
            else:
                remote_filepath = self.remote_path + os.path.relpath(filepath, self.upload_item_element)

            self.type = 'file'
            self.buffer = filepath
            self.remote_filepath = remote_filepath.replace("\\", "/")
            self.annotations_filepath = annotations_filepath


class FileUploadElement(BaseUploadElement):

    def __init__(self, all_upload_elements: dict):
        super().__init__(all_upload_elements)

        filepath = self.upload_item_element
        # extract item's size
        self.total_size += os.path.getsize(filepath)
        # determine item's remote base name
        if self.remote_name is None:
            self.remote_name = os.path.basename(filepath)
        # get annotations file
        if self.upload_annotations_element is not None:
            # change path to annotations
            annotations_filepath = filepath.replace(self.upload_item_element, self.upload_annotations_element)
            # remove image extension
            annotations_filepath, _ = os.path.splitext(annotations_filepath)
            # add json extension
            annotations_filepath += ".json"
        else:
            annotations_filepath = None
        # append to list
        remote_filepath = self.remote_path + self.remote_name
        self.type = 'file'
        self.buffer = filepath
        self.remote_filepath = remote_filepath
        self.annotations_filepath = annotations_filepath


class ItemLinkUploadElement(BaseUploadElement):

    def __init__(self, all_upload_elements: dict):
        super().__init__(all_upload_elements)

        link = entities.Link(ref=self.upload_item_element.id, type='id', dataset_id=self.upload_item_element.datasetId,
                             name='{}_link.json'.format(self.upload_item_element.name))
        if self.remote_name is None:
            self.remote_name = link.name

        remote_filepath = '{}{}'.format(self.remote_path, self.remote_name)
        self.type = 'link'
        self.buffer = link
        self.remote_filepath = remote_filepath
        self.annotations_filepath = self.upload_annotations_element


class LinkUploadElement(BaseUploadElement):

    def __init__(self, all_upload_elements: dict):
        super().__init__(all_upload_elements)

        if self.remote_name is None:
            self.remote_name = self.upload_item_element.name

        remote_filepath = '{}{}_link.json'.format(self.remote_path, self.remote_name)
        self.type = 'link'
        self.buffer = self.upload_item_element
        self.remote_filepath = remote_filepath
        self.annotations_filepath = self.upload_annotations_element


class MultiViewUploadElement(BaseUploadElement):

    def __init__(self, all_upload_elements: dict):
        super().__init__(all_upload_elements)

        if self.remote_name:
            self.upload_item_element.name = self.remote_name

        if not self.upload_item_element.name.endswith('.json'):
            self.upload_item_element.name = '{}.json'.format(self.upload_item_element.name)

        remote_filepath = '{}{}'.format(self.remote_path, self.upload_item_element.name)
        self.type = 'collection'
        self.buffer = self.upload_item_element
        self.remote_filepath = remote_filepath
        self.annotations_filepath = self.upload_annotations_element


class SimilarityUploadElement(BaseUploadElement):

    def __init__(self, all_upload_elements: dict):
        super().__init__(all_upload_elements)

        if self.remote_name:
            self.upload_item_element.name = self.remote_name
        if self.upload_item_element.name is None:
            self.upload_item_element.name = '{}_similarity.json'.format(self.upload_item_element.ref)

        if not self.upload_item_element.name.endswith('.json'):
            remote_filepath = '{}{}.json'.format(self.remote_path, self.upload_item_element.name)
        else:
            remote_filepath = '{}{}'.format(self.remote_path, self.upload_item_element.name)

        self.type = 'collection'
        self.buffer = self.upload_item_element
        self.remote_filepath = remote_filepath
        self.annotations_filepath = self.upload_annotations_element


class UrlUploadElement(BaseUploadElement):

    def __init__(self, all_upload_elements: dict):
        super().__init__(all_upload_elements)

        # noinspection PyTypeChecker
        if self.remote_name is None:
            self.remote_name = str(self.upload_item_element.split('/')[-1]).split('?')[0]

        remote_filepath = self.remote_path + self.remote_name
        self.type = 'url'
        self.buffer = self.upload_item_element
        self.remote_filepath = remote_filepath
        self.annotations_filepath = self.upload_annotations_element


class DataFrameUploadElement(BaseUploadElement):

    def __init__(self, all_upload_elements: dict):
        super().__init__(all_upload_elements)

        if not self.remote_path.endswith('/'):
            self.remote_path += '/'

        if os.path.isfile(self.upload_item_element):
            element_type = 'file'
            if self.remote_name is None:
                self.remote_name = os.path.basename(self.upload_item_element)
        elif self.is_url(self.upload_item_element):
            element_type = 'url'
            if self.remote_name is None:
                self.remote_name = str(self.upload_item_element.split('/')[-1])
        else:
            raise PlatformException("404", "Unknown local path: {}".format(self.upload_item_element))
        self.type = element_type
        self.buffer = self.upload_item_element
        self.remote_filepath = self.remote_path + self.remote_name

    def is_url(self, url):
        try:
            return validators.url(url)
        except Exception:
            return False
