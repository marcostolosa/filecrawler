import re

from filecrawler.rulebase import RuleBase


class UrlCreds(RuleBase):

    def __init__(self):
        super().__init__('url-creds', 'URL Credentials')

        self._regex = re.compile(r"([a-zA-Z0-9_-]{2,30}://[^@:/\n\"' ]{1,256}:[^@:/\n\"' ]{1,256}@[a-zA-Z0-9._-]{2,256}.[a-zA-Z0-9.]{2,256}[:0-9]{0,6})")
        # (?![A-Za-z0-9:._-])
        self._keywords = ["://"]
        self._fp_regex = re.compile(r"[a-zA-Z0-9_-]{2,30}://([<]{0,1})(user|username|usuario)([>]{0,1}):([<]{0,1})(pass|password|token|secret|senha)([>]{0,1})@")
        self._exclude_keywords = [
            "\n"  # Cannot exists break line
            "sqlserver://",
            "smtp://"
        ]

        self._tps = [
            self.generate_sample_secret("url", "http://file:crawler@domain.com.br:8080"),
            self.generate_sample_secret("url", "https://file:crawler@domain.com:8080"),
            self.generate_sample_secret("url", "ftp://file:crawler@domain.com")

        ]

        self._fps = [
            self.generate_sample_secret("url", "http://domain.com.br:8080/\nteste@123.com"),
            self.generate_sample_secret("url", "http://domain.com.br:8080\nteste@123.com"),
            self.generate_sample_secret("url", "http://domain.com.br\nteste@123.com"),
            self.generate_sample_secret("url", "http://domain.com.br teste@123.com"),
            self.generate_sample_secret("url", "http://user:pass@domain.com.br"),
            self.generate_sample_secret("url", "http://<username>:<password>@domain.com.br"),
            self.generate_sample_secret("url", "http://<username>:<token>@domain.com.br")
        ]

    def post_processor(self, original_data: str, found: str) -> dict:
        try:
            p = re.compile(
                r"[a-zA-Z0-9_-]{2,30}://([^@:]{1,256}):([^@:/\n\"']{1,256})@")

            severity = 100

            m = p.match(found)
            if not m:
                return {}

            username = m.group(1)
            password = m.group(2)
            entropy = self.entropy(password)

            if username.strip() == '' or password.strip() == '':
                return {}

            if password[0:1] == '$':
                severity = 70

            if entropy <= 0.7:
                severity = 30

            if len(username) <= 2 or len(password) <= 2:
                return {}

            return dict(
                username=username,
                password=password,
                severity=severity,
                entropy=entropy
            )

        except:
            return {}
