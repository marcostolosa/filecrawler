import json
import sys
from argparse import _ArgumentGroup, Namespace

from filecrawler._exceptions import IntegrationError
from filecrawler.config import Configuration
from filecrawler.crawlerbase import CrawlerBase
from filecrawler.libs.color import Color
from elasticsearch import Elasticsearch
import requests
import elastic_transport

requests.packages.urllib3.disable_warnings()


class Elastic(CrawlerBase):
    nodes = []
    _CREDS_WHITE_LIST = []

    def __init__(self):
        super().__init__('elastic', 'Integrate to elasticsearch')

    def add_flags(self, flags: _ArgumentGroup):
        pass

    def add_commands(self, cmds: _ArgumentGroup):
        pass

    def get_config_sample(self) -> dict:
        return {
            'elasticsearch': {
                'nodes': [{'url': 'http://127.0.0.1:9200'}],
                #'bulk_size': 200,
                #'byte_size': '500K',
                #'flush_interval': '2s'
            }
        }

    def load_from_arguments(self, args: Namespace) -> bool:
        return True

    def load_config(self, config: dict) -> bool:
        # Change log level
        import warnings
        from elasticsearch.exceptions import ElasticsearchWarning
        warnings.simplefilter('ignore', ElasticsearchWarning)

        import validators
        from urllib.parse import urlparse
        if config is not None and config.get('elasticsearch', None) is not None:
            elasticsearch = config.get('elasticsearch', {})

            try:
                self.nodes = [
                    {
                        'scheme': url.scheme,
                        'host': f'{url.netloc}:'.split(':', 1)[0],
                        'port': int((url.netloc.split(':')[1:2] or (9200,))[0])
                    }
                    for url in [
                        urlparse(n['url']) for n in elasticsearch.get('nodes', [])
                        if n.get('url', None) is not None and validators.url(n['url'])
                    ]
                ]
            except Exception as e:
                Color.pl('{!} {R}error parsing elastic nodes: {O}%s{W}\r\n' % str(e))
                sys.exit(1)

        if self.nodes is None or len(self.nodes) == 0:
            Color.pl('{!} {R}error: invalid elasticsearch nodes. Check configuration file.{W}\r\n')
            sys.exit(1)

        return True

    def pre_run(self, **data):
        es = Elasticsearch(self.nodes)
        if not es.indices.exists(index=Configuration.index_name):
            request_body = {
                "settings": {
                    "number_of_replicas": 1,
                    "index": {"highlight.max_analyzed_offset": 10000000}
                },

                'mappings': {
                    'properties': {
                        'indexing_date': {'type': 'date'},
                        'created': {'type': 'date'},
                        'last_accessed': {'type': 'date'},
                        'last_modified': {'type': 'date'},
                        'fingerprint': {'type': 'keyword'},
                        'filename': {'type': 'text'},
                        'extension': {'type': 'keyword'},
                        'mime_type': {'type': 'keyword'},
                        'file_size': {'type': 'long'},
                        'path_virtual': {'type': 'text'},
                        'path_real': {'type': 'text'},
                        'content': {'type': 'text'},
                        'filtered_content': {'type': 'text'},
                        'metadata': {'type': 'text'},
                        'has_credential': {'type': 'boolean'},
                        'parser': {'type': 'keyword'},
                        'object_content': {'type': 'text'},
                        'info': {'type': 'text'},
                        'credentials': {'type': 'flattened'},
                    }
                }
            }

            es.indices.create(
                index=Configuration.index_name,
                body=request_body
            )

        request_body = {
            "settings": {
                "number_of_replicas": 1,
                "index": {"highlight.max_analyzed_offset": 10000000}
            },

            'mappings': {
                'properties': {
                    'indexing_date': {'type': 'date'},
                    'created': {'type': 'date'},
                    'fingerprint': {'type': 'keyword'},
                    'match': {'type': 'keyword'},
                    'content': {'type': 'text'},
                    'info': {'type': 'text'},
                    'filtered_file': {'type': 'text'},
                    'rule': {'type': 'keyword'},
                    'username': {'type': 'keyword'},
                    'password': {'type': 'keyword'},
                    'domain': {'type': 'keyword'},
                    'aws_access_key': {'type': 'keyword'},
                    'aws_access_secret': {'type': 'keyword'},
                    'aws_region': {'type': 'keyword'},
                    'token': {'type': 'keyword'},
                    'severity': {'type': 'double'},
                    'entropy': {'type': 'double'},
                }
            }
        }

        # Update permitted list
        Elastic._CREDS_WHITE_LIST = [
            f.lower()
            for f, _ in request_body['mappings']['properties'].items()
        ]

        if not es.indices.exists(index=Configuration.index_name + '_credentials'):
            es.indices.create(
                index=Configuration.index_name + '_credentials',
                body=request_body
            )

    def integrate(self, **data):
        try:

            id = data['fingerprint']
            if Configuration.filename_as_id:
                id = data['path_virtual']

            with(Elasticsearch(self.nodes, timeout=30, max_retries=10, retry_on_timeout=True)) as es:
                res = es.index(index=Configuration.index_name, id=id, document=data)
                if res is None or res.get('_shards', {}).get('successful', 0) == 0:
                    if not Configuration.continue_on_error:
                        raise Exception(f'Cannot insert elasticsearch data: {res}')

                #if res.get('result', '') != 'created':
                #    Logger.pl(res)

                # Index only credentials
                findings = CrawlerBase.get_credentials_data(data)

                for k, f in findings.items():
                    try:
                        j_data = json.loads(f.get('content', '{}'))
                        if isinstance(j_data, dict):
                            f.update({
                                k1: v1
                                for k1, v1 in j_data.items()
                                if k1.lower() in Elastic._CREDS_WHITE_LIST
                            })
                    except:
                        pass

                    try:
                        # Filter just the first 50 lines
                        ff = f.get('filtered_file', None)
                        if ff is not None:
                            f['filtered_file'] = '\n'.join(ff.split('\n')[0:50])
                    except:
                        pass

                    res = es.index(index=Configuration.index_name + '_credentials', id=k, document=f)
                    if res is None or res.get('_shards', {}).get('successful', 0) == 0:
                        if not Configuration.continue_on_error:
                            raise Exception(f'Cannot insert elasticsearch data: {res}')

        except (elastic_transport.ConnectionError, requests.exceptions.ConnectionError) as e:
            raise IntegrationError(e)











