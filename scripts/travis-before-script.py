import codecs
import os

from jinja2 import Environment, FileSystemLoader


env = Environment(
    loader=FileSystemLoader(
        os.path.join(
            os.path.dirname(__file__), "../provisioning/roles/kuma/templates"
        )
    )
)
template = env.get_template('Index.xml.j2')

with codecs.open('/usr/share/mysql/charsets/Index.xml', 'w', encoding='utf-8') as f:
    f.write(template.render(collation_id=999))
