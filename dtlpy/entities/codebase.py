import logging
import os

from .. import entities, repositories

logger = logging.getLogger(name='dtlpy')


class PackageCodebaseType:
    ITEM = 'item'
    GIT = 'git'
    FILESYSTEM = 'filesystem'
    LOCAL = 'local'


class Codebase:
    def __init__(self,
                 package_codebase_type=PackageCodebaseType.ITEM,
                 client_api=None):
        self.type = package_codebase_type
        self._client_api = client_api

    def __str__(self):
        return str(self.to_json())

    def to_json(self):
        _json = {'type': self.type}
        return _json

    @staticmethod
    def from_json(_json: dict, client_api):
        """
        :param client_api: ApiClient entity
        """
        if _json['type'] == PackageCodebaseType.GIT:
            cls = GitCodebase.from_json(_json=_json,
                                        client_api=client_api)
        elif _json['type'] == PackageCodebaseType.ITEM:
            cls = ItemCodebase.from_json(_json=_json,
                                         client_api=client_api)
        elif _json['type'] == PackageCodebaseType.FILESYSTEM:
            cls = FilesystemCodebase.from_json(_json=_json,
                                               client_api=client_api)
        elif _json['type'] == PackageCodebaseType.LOCAL:
            cls = LocalCodebase.from_json(_json=_json,
                                          client_api=client_api)
        else:
            raise ValueError('[Codebase constructor] Unknown codebase type: {}'.format(_json['type']))
        return cls

    @property
    def is_remote(self):
        """ Return whether the codebase is managed remotely and supports upload-download"""
        return self.type in [PackageCodebaseType.ITEM, PackageCodebaseType.GIT]

    @property
    def is_local(self):
        """ Return whether the codebase is locally and has no management implementations"""
        return not self.is_remote


class GitCodebase(Codebase):
    def __init__(self, git_url: str, git_tag: str, credentials=None):
        super().__init__(package_codebase_type=PackageCodebaseType.GIT)
        self.git_url = git_url if git_url.endswith('.git') else git_url + '.git'
        self.git_tag = git_tag
        self.credentials = credentials
        self._codebases = None

        # add .git prefix to the url
        if git_url.endswith('.git'):
            self.git_url = git_url
        else:
            self.git_url = git_url + '.git'

        if git_tag is None:
            logger.warning("git_tag param not provided. Using 'master'!")
            git_tag = 'master'
        self.git_tag = git_tag

    @property
    def codebases(self):
        if self._codebases is None:
            self._codebases = repositories.Codebases(client_api=self._client_api)
        assert isinstance(self._codebases, repositories.Codebases)
        return self._codebases

    def to_json(self):
        _json = super().to_json()
        _json['gitUrl'] = self.git_url
        _json['gitTag'] = self.git_tag

        if self.credentials is not None:
            _json['credentials'] = self.credentials

        return _json

    @classmethod
    def from_json(cls, _json: dict, client_api):
        """
        :param _json: platform json
        :param client_api: ApiClient entity
        """
        return cls(
            git_url=_json.get('gitUrl'),
            git_tag=_json.get('gitTag'),
            credentials=_json.get('credentials', None),
        )

    @property
    def git_user_name(self):
        return self.git_url.split('/')[-2]

    @property
    def git_repo_name(self):
        last = self.git_url.split('/')[-1]
        return os.path.splitext(last)[0]

    @property
    def git_username(self):
        if self.credentials is not None:
            return os.environ.get(
                self.credentials.get('username', {}).get('key', ''),
                None
            )
        return None

    @property
    def git_password(self):
        if self.credentials is not None:
            return os.environ.get(
                self.credentials.get('password', {}).get('key', ''),
                None
            )
        return None

    @staticmethod
    def is_git_repo(path):
        """
        :param path: `str` TODO: Currently only for local folder
        :return: `bool` testing if the path is valid git repo
        """
        return os.path.isdir(os.path.join(path, '.git'))

    def unpack(self, local_path):
        """
        Clones the git codebase
        :param local_path:
        """

        return self.codebases.clone_git(
            codebase=self,
            local_path=local_path
        )


class LocalCodebase(Codebase):
    def __init__(self, local_path: str = None):
        super().__init__(package_codebase_type=PackageCodebaseType.LOCAL)
        self._local_path = local_path

    def to_json(self):
        _json = super().to_json()
        if self._local_path is not None:
            _json['localPath'] = self._local_path
        return _json

    @property
    def local_path(self):
        return os.path.expandvars(self._local_path)

    @local_path.setter
    def local_path(self, local_path: str):
        self._local_path = local_path

    @classmethod
    def from_json(cls, _json: dict, client_api):
        """
        :param _json: platform json
        :param client_api: ApiClient entity
        """
        return cls(
            local_path=_json.get('localPath', None),
        )


class FilesystemCodebase(Codebase):
    def __init__(self, container_path: str = None, host_path: str = None):
        super().__init__(package_codebase_type=PackageCodebaseType.FILESYSTEM)
        self.host_path = host_path
        self.container_path = container_path

    def to_json(self):
        _json = super().to_json()
        if self.host_path is not None:
            _json['hostPath'] = self.host_path
        if self.container_path is not None:
            _json['containerPath'] = self.container_path
        return _json

    @classmethod
    def from_json(cls, _json: dict, client_api):
        """
        :param _json: platform json
        :param client_api: ApiClient entity
        """
        return cls(
            container_path=_json.get('containerPath', None),
            host_path=_json.get('hostPath', None)
        )


class ItemCodebase(Codebase):
    def __init__(self, item_id: str, client_api=None, item=None):
        super().__init__()
        self.item_id = item_id
        self._item = item
        self._client_api = client_api
        self._codebases = None

    @property
    def codebases(self):
        if self._codebases is None:
            self._codebases = repositories.Codebases(client_api=self._client_api,
                                                     dataset=self.item.dataset)
        assert isinstance(self._codebases, repositories.Codebases)
        return self._codebases

    def to_json(self) -> dict:
        _json = super().to_json()
        _json['itemId'] = self.item_id
        return _json

    @property
    def item(self):
        if self._item is None:
            self._item = repositories.Items(client_api=self._client_api).get(item_id=self.item_id)
        assert isinstance(self._item, entities.Item)
        return self._item

    @classmethod
    def from_json(cls, _json: dict, client_api):
        """
        :param _json: platform json
        :param client_api: ApiClient entity
        """
        return cls(
            item_id=_json['itemId'],
            client_api=client_api
        )

    def unpack(self, local_path):
        """
        Clones the git codebase
        :param local_path:
        """
        return self.codebases.unpack(
            codebase_id=self.item_id,
            local_path=local_path
        )

    @property
    def version(self):
        return str(self.item.name.split('.')[0])

    @property
    def md5(self):
        md5 = None
        if 'system' in self.item.metadata:
            md5 = self.item.metadata['system'].get('md5', None)
        return md5

    @md5.setter
    def md5(self, md5):
        if 'system' not in self.item.metadata:
            self.item.metadata['system'] = dict()
        self.item.metadata['system']['md5'] = md5

    @property
    def description(self):
        description = None
        if 'system' in self.item.metadata:
            description = self.item.metadata['system'].get('description', None)
        return description

    @description.setter
    def description(self, description):
        if 'system' not in self.item.metadata:
            self.item.metadata['system'] = dict()
        self.item.metadata['system']['description'] = description

    def list_versions(self):
        """
        List Codebase versions
        """
        # get codebase name
        codebase_name = self.item.filename.split('/')[len(self.item.filename.split('/')) - 2]
        return self.codebases.list_versions(codebase_name=codebase_name)
