

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Dict, Tuple, Union

import re

import base64
import json
import io
import os
import yaml
import requests

from http import HTTPStatus
from urllib.parse import quote

from ccai.errors.exceptions import PublishError

from ccai.configuration.synchronization.configsynchronizerbase import ConfigSynchronizerBase

GITHUB_API_VERSION = "2022-11-28"

DEFAULT_GITHUB_CONFIG_BRANCH = "main"

class GithubConfigSynchronizer(ConfigSynchronizerBase):
    """
        A GitHub repository configuration synchronizer.

        github://some-owner/some-repo/some/base/path

        ..note: For GitHub, the configurations are stored as files committed to a branch (``main`` by default) of the
                repository named in the storage-uri.  The ``leaf`` portion of the storage-uri is the base path inside
                the repository and the files are laid out with the same venue/user/class structure that the other
                synchronizers use, ``<leaf>/<venue>/<user>/<config-class>/<config-name>.<format>``.  For example,
                'configs/azure/myron/landscapes/apod-picluster.yaml'.  Publishing commits the file to the branch
                through the git-data API and retrieval reads the same file from the same branch through the
                contents API, so a published configuration is immediately retrievable.
    """

    scheme = "github"
    parse_exp = re.compile(r"github://(?P<owner>[a-zA-Z\.0-9\-]+)/(?P<repo>[a-zA-Z\.0-9\-]+)/(?P<leaf>[\S]+)")

    def __init__(self, storage_uri: str, owner: str, repo: str, leaf: str, branch: str = DEFAULT_GITHUB_CONFIG_BRANCH):
        """
            Initializes a GitHub based configuration synchronizer.

            :param storage_uri: Source URI string.
            :param owner: Repository owner name.
            :param repo: Repository name.
            :param leaf: Base path for configuration files inside the repository.
            :param branch: The branch that configurations are published to and retrieved from.
        """
        super().__init__(storage_uri)

        self._owner = owner
        self._repo = repo
        self._leaf = leaf
        self._branch = branch
        return

    @classmethod
    def parse(cls, uri: str) -> Union[None, "GithubConfigSynchronizer"]:
        """
            Parses a GitHub synchronizer URI.

            :param uri: URI to parse.

            :returns: A :class:`GithubConfigSynchronizer` instance or ``None``.
        """

        rtnobj = None

        mobj = cls.parse_exp.match(uri)
        if mobj is not None:
            matchinfo = mobj.groupdict()

            owner = matchinfo["owner"]
            repo = matchinfo["repo"]
            leaf = matchinfo["leaf"]

            rtnobj = GithubConfigSynchronizer(uri, owner, repo, leaf)

        return rtnobj

    def _create_request_headers(self, credentials: Dict[str, Tuple[str, str]]) -> Dict[str, str]:
        """
            Creates the headers used for GitHub REST API requests.

            :param credentials: Mapping of host to ``(user, token)`` pairs.

            :returns: A dictionary of request headers.
        """

        username, token = credentials[self._owner]

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": GITHUB_API_VERSION
        }

        return headers

    def _get_config_repository_path(self, venue: str, user: str, config_class: str, config_name: str, config_format: str) -> str:
        """
            Gets the path, relative to the root of the repository, where a configuration file is stored.  Publishing
            and retrieval both use this path so a published configuration can be retrieved.

            ..note: The path does not start with a '/' because GitHub rejects git tree entry paths that do.

            :param venue: Venue identifier for the configuration.
            :param user: User name used to namespace the configuration.
            :param config_class: Configuration class folder name.
            :param config_name: Name of the configuration document.
            :param config_format: File format ``json`` or ``yaml``.

            :returns: The repository relative path of the configuration file.
        """

        path_parts = []

        leaf = self._leaf.strip("/")
        if len(leaf) > 0:
            path_parts.append(leaf)

        path_parts.extend([venue, user, config_class, f"{config_name}.{config_format}"])

        repository_path = "/".join(path_parts)

        return repository_path

    def _publish_configuration(self, venue: str, user: str, config_class: str, config_name: str, config_format: str, config_info: str, credentials: Dict[str, Tuple[str, str]]):
        """
            Publish a configuration file to GitHub by committing it to the configuration branch at the path given
            by :meth:`_get_config_repository_path`.

            :param venue: Venue identifier for the configuration.
            :param user: User name used to namespace the configuration.
            :param config_class: Configuration class folder name.
            :param config_name: Name of the configuration document.
            :param config_format: File format ``json`` or ``yaml``.
            :param config_info: Configuration data to persist.
            :param credentials: Mapping of host to ``(user, token)`` pairs.

            :raises: PublishError
        """
        
        headers = self._create_request_headers(credentials)

        ref = f"heads/{self._branch}"

        publish_path = self._get_config_repository_path(venue, user, config_class, config_name, config_format)

        # Step 1 - Get a reference to the head revision 
        ref_url = f"https://api.github.com/repos/{self._owner}/{self._repo}/git/ref/{ref}"
        resp: requests.Response = requests.get(ref_url, headers=headers)
        if resp.status_code != HTTPStatus.OK:
            errmsg = f"Failed to get a reference to branch. ref={ref}"
            raise PublishError(errmsg)

        ref_info = resp.json()

        ref_obj = ref_info["object"]
        top_commit_url = ref_obj["url"]

        # Step 2 - Get the top commit info
        resp: requests.Response = requests.get(top_commit_url, headers=headers)
        if resp.status_code != HTTPStatus.OK:
            errmsg = f"Failed to get the top commit for branch. ref={ref}"
            raise PublishError(errmsg)

        commit_info = resp.json()

        commit_sha = commit_info["sha"]
        commit_tree = commit_info["tree"]
        commit_tree_url = commit_tree["url"]

        # Step 3 - Post a blob of the commit to github
        commit_content_buffer = io.StringIO()
        if config_format == "yaml":
            yaml.safe_dump(config_info, commit_content_buffer, indent=4)
        elif config_format == "json":
            json.dump(config_info, commit_content_buffer, indent=4)
        else:
            errmsg = f"Error publishing config '{config_name}' due to unsupported format. config_format={config_format}"
            raise PublishError(errmsg)

        commit_content = commit_content_buffer.getvalue()

        blob_info = {
            "content": base64.b64encode(commit_content.encode("utf-8")).decode("ascii"),
            "encoding": "base64"
        }

        # GitHub "create a blob" (POST .../git/blobs) responds with 201 Created.
        blobs_post_url = f"https://api.github.com/repos/{self._owner}/{self._repo}/git/blobs"
        resp: requests.Response = requests.post(blobs_post_url, headers=headers, json=blob_info)
        if resp.status_code != HTTPStatus.CREATED:
            errmsg = f"Failed to post a blob for config. config_name={config_name}"
            raise PublishError(errmsg)
        
        blob_info = resp.json()
        blob_sha = blob_info["sha"]

        # Step 4 - Get a hold of the tree of the top commit
        resp: requests.Response = requests.get(commit_tree_url, headers=headers)
        if resp.status_code != HTTPStatus.OK:
            errmsg = f"Failed to get the tree associated with the top commit for branch. ref={ref}"
            raise PublishError(errmsg)

        top_commit_tree_info = resp.json()
        top_commit_tree_sha = top_commit_tree_info["sha"]

        # Step 5 - Create a commit tree for the publish commit
        create_commit_tree_body = {
            "base_tree": top_commit_tree_sha,
            "tree": [
                {
                    "path": publish_path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha
                }
            ]
        }

        create_commit_tree_url = f"https://api.github.com/repos/{self._owner}/{self._repo}/git/trees"
        resp: requests.Response = requests.post(create_commit_tree_url, json=create_commit_tree_body, headers=headers)
        if resp.status_code != HTTPStatus.CREATED:
            errmsg = f"Failed to create a commit tree for the publish commmit. config_name={config_name}"
            raise PublishError(errmsg)

        publish_commit_tree_info = resp.json()
        publish_commit_tree_sha = publish_commit_tree_info["sha"]

        commit_message = f"Publish {config_class} configuration '{config_name}' for user '{user}' and venue '{venue}' to '{publish_path}'."

        # Step 6 - Create the new commit.
        publish_commit = {
            "message": commit_message,
            "parents": [commit_sha],
            "tree": publish_commit_tree_sha
        }

        publish_commit_url = f"https://api.github.com/repos/{self._owner}/{self._repo}/git/commits"
        resp: requests.Response = requests.post(publish_commit_url, json=publish_commit, headers=headers)
        if resp.status_code != HTTPStatus.CREATED:
            errmsg = f"Failed to create a configuration commit. config_name={config_name}"
            raise PublishError(errmsg)
        
        publish_response_info = resp.json()

        publish_commit_sha = publish_response_info["sha"]

        # Step 7 - Update head to point to our publish commit
        move_head_body = {
            "sha": publish_commit_sha,
            "force": False
        }

        # GitHub "update a reference" is PATCH .../git/refs/{ref} (plural 'refs'; the singular
        # '.../git/ref/{ref}' used in Step 1 is the read-only endpoint) and responds with 200 OK.
        update_ref_url = f"https://api.github.com/repos/{self._owner}/{self._repo}/git/refs/{ref}"
        resp: requests.Response = requests.patch(update_ref_url, json=move_head_body, headers=headers)
        if resp.status_code != HTTPStatus.OK:
            errmsg = f"Failed to move HEAD to our commit for branch. ref={ref} config_name={config_name}"
            raise PublishError(errmsg)

        return
    
    def _retrieve_configuration(self, venue: str, user: str, config_class: str, config_name: str, credentials: Dict[str, Tuple[str, str]]) -> Union[Tuple[str, dict], Tuple[None, None]]:
        """
            Retrieve a configuration file from GitHub.  The file is read from the same branch and repository path
            that :meth:`_publish_configuration` commits it to.

            :param venue: Venue identifier for the configuration.
            :param user: User name used to namespace the configuration.
            :param config_class: Configuration class folder name.
            :param config_name: Name of the configuration document.
            :param credentials: Mapping of host to ``(user, token)`` pairs.

            :returns: Tuple of configuration format and configuration data or ``(None, None)``.
            :raises: RuntimeError
        """

        config_format = None
        config_info = None

        headers = self._create_request_headers(credentials)

        yaml_content = self._retrieve_repository_file(venue, user, config_class, config_name, "yaml", headers)
        if yaml_content is not None:
            config_buffer = io.StringIO(yaml_content)
            config_info = yaml.safe_load(config_buffer)
            config_format = "yaml"
        else:
            json_content = self._retrieve_repository_file(venue, user, config_class, config_name, "json", headers)
            if json_content is not None:
                config_buffer = io.StringIO(json_content)
                config_info = json.load(config_buffer)
                config_format = "json"

        return config_format, config_info

    def _retrieve_repository_file(self, venue: str, user: str, config_class: str, config_name: str, config_format: str,
                                  headers: Dict[str, str]) -> Union[str, None]:
        """
            Retrieves the content of a configuration file from the configuration branch of the repository using the
            GitHub contents API.

            :param venue: Venue identifier for the configuration.
            :param user: User name used to namespace the configuration.
            :param config_class: Configuration class folder name.
            :param config_name: Name of the configuration document.
            :param config_format: File format ``json`` or ``yaml``.
            :param headers: The GitHub REST API request headers.

            :returns: The text content of the file or ``None`` if the file does not exist.
            :raises: RuntimeError
        """

        file_content = None

        repository_path = self._get_config_repository_path(venue, user, config_class, config_name, config_format)

        quoted_path = quote(repository_path)
        quoted_branch = quote(self._branch)
        retrieve_url = f"https://api.github.com/repos/{self._owner}/{self._repo}/contents/{quoted_path}?ref={quoted_branch}"

        resp: requests.Response = requests.get(retrieve_url, headers=headers)
        if resp.status_code == HTTPStatus.OK:
            content_info = resp.json()

            content_encoding = content_info.get("encoding")
            if content_encoding == "base64":
                encoded_content = content_info["content"]
                file_content = base64.b64decode(encoded_content).decode("utf-8")
            else:
                err_msg_lines = [
                    "Unable to retrieve a configuration file from GitHub because the content was not returned base64 encoded.",
                    f"    OWNER: {self._owner}",
                    f"    REPO: {self._repo}",
                    f"    BRANCH: {self._branch}",
                    f"    PATH: {repository_path}",
                    f"    ENCODING: {content_encoding}",
                    "NOTE: The GitHub contents API only returns content for files up to 1 MB.",
                ]
                errmsg = os.linesep.join(err_msg_lines)
                raise RuntimeError(errmsg)

        elif resp.status_code != HTTPStatus.NOT_FOUND:
            err_msg_lines = [
                "Unexpected status code while retrieving a configuration file from GitHub.",
                f"    OWNER: {self._owner}",
                f"    REPO: {self._repo}",
                f"    BRANCH: {self._branch}",
                f"    PATH: {repository_path}",
                f"    STATUS: {resp.status_code}",
            ]
            errmsg = os.linesep.join(err_msg_lines)
            raise RuntimeError(errmsg)

        return file_content
