import six
from lxml import etree


class StorageConfigObject(object):

    def __init__(self, **kwargs):
        super(StorageConfigObject, self).__init__()

        self.root_name = kwargs.get("root_name")

    def _new_node(self, node_name, **kwargs):
        return etree.Element(node_name, **kwargs)

    def _text_node(self, node_name, value, **kwargs):
        child = etree.Element(node_name, **kwargs)
        child.text = six.text_type(value)
        return child

    def format_dom(self):
        return self._new_node(self.root_name)

    def parse_str(self, xmlstr):
        self.parse_dom(etree.fromstring(xmlstr))

    def parse_dom(self, xmldoc):
        if self.root_name != xmldoc.tag:
            msg = ("Root element name should be '%(name)s' not '%(tag)s'" %
                   {'name': self.root_name, 'tag': xmldoc.tag})
            raise Exception(msg)

    def to_xml(self, pretty_print=True):
        root = self.format_dom()
        xml_str = etree.tostring(root, encoding='unicode',
                                 pretty_print=pretty_print)
        return xml_str


class LibvirtConfigStorage(StorageConfigObject):

    def __init__(self, **kwargs):
        super(LibvirtConfigStorage, self).__init__(root_name='pool', **kwargs)

        self.type = "dir"
        self.name = None
        self.uuid = None
        self.source = None
        self.target_path = None

    def _format_target(self, storage):
        target = etree.Element('target')
        if self.target_path:
            target.append(self._text_node("path", self.target_path))
        permission = etree.Element('permissions')
        permission.append(self._text_node("mode", "0777"))
        target.append(permission)
        storage.append(target)

    def format_dom(self):
        storage = super(LibvirtConfigStorage, self).format_dom()
        storage.append(self._text_node("uuid", self.uuid))
        storage.append(self._text_node("name", self.name))
        if self.type is not None:
            storage.set('type', self.type)

        storage.append(self._text_node("source", ''))
        self._format_target(storage)
        return storage
