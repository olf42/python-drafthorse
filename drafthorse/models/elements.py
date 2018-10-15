import sys
from decimal import Decimal

from datetime import date, datetime

import xml.etree.cElementTree as ET
from collections import OrderedDict

from drafthorse.utils import validate_xml

from . import NS_UDT
from .fields import Field
from .container import Container


class BaseElementMeta(type):
    def __new__(mcls, name, bases, attrs):
        cls = super(BaseElementMeta, mcls).__new__(mcls, name, bases, attrs)
        fields = list(cls._fields) if hasattr(cls, '_fields') else []
        for attr, obj in attrs.items():
            if isinstance(obj, Field):
                if sys.version_info < (3, 6):
                    obj.__set_name__(cls, attr)
                fields.append(obj)
        cls._fields = fields
        return cls


class Element(metaclass=BaseElementMeta):
    def __init__(self, **kwargs):
        self._data = OrderedDict([
            (f.name, f.initialize() if f.default else None) for f in self._fields
        ])
        for k, v in kwargs.items():
            setattr(self, k, v)

    def _etree_node(self):
        node = ET.Element(self.get_tag())
        if hasattr(self, 'Meta') and hasattr(self.Meta, 'attributes'):
            for k, v in self.Meta.attributes.items():
                node.set(k, v)
        return node

    def to_etree(self):
        node = self._etree_node()
        for v in self._data.values():
            if v is not None:
                v.append_to(node)
        return node

    def get_tag(self):
        return "{%s}%s" % (self.Meta.namespace, self.Meta.tag)

    def append_to(self, node):
        node.append(self.to_etree())

    def serialize(self):
        xml = b"<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + ET.tostring(self.to_etree(), "utf-8")
        validate_xml(xmlout=xml, schema="ZUGFeRD1p0")
        return xml

    def from_etree(self, root):
        if hasattr(self, 'Meta') and hasattr(self.Meta, 'namespace') and root.tag != "{%s}%s" % (self.Meta.namespace, self.Meta.tag):
            raise TypeError("Invalid XML, found tag {} where {} was expected".format(root.tag, "{%s}%s" % (self.Meta.namespace, self.Meta.tag)))
        field_index = {}
        for field in self._fields:
            element = getattr(self, field.name)
            field_index[element.get_tag()] = (field.name, element)
        for child in root:
            if child.tag in field_index:
                name, childel = field_index[child.tag]
                if isinstance(getattr(self, name), Container):
                    getattr(self, name).add_from_etree(child)
                else:
                    getattr(self, name).from_etree(child)
            else:
                raise TypeError("Unknown element {}".format(child.tag))
        return self

    @classmethod
    def parse(cls, xmlinput):
        from lxml import etree
        root = etree.fromstring(xmlinput)
        return cls().from_etree(root)


class StringElement(Element):
    def __init__(self, namespace, tag, text=""):
        super().__init__()
        self.namespace = namespace
        self.tag = tag
        self.text = text

    def __str__(self):
        return self.text

    def get_tag(self):
        return "{%s}%s" % (self.namespace, self.tag)

    def to_etree(self):
        node = self._etree_node()
        node.text = self.text
        return node

    def from_etree(self, root):
        self.text = root.text
        return self


class DecimalElement(StringElement):
    def __init__(self, namespace, tag, value=0):
        super().__init__(namespace, tag)
        self.value = value

    def to_etree(self):
        node = self._etree_node()
        node.text = str(self.value)
        return node

    def __str__(self):
        return self.value

    def from_etree(self, root):
        self.value = Decimal(root.text)
        return self


class QuantityElement(StringElement):
    def __init__(self, namespace, tag, amount="", unit_code=""):
        super().__init__(namespace, tag)
        self.amount = amount
        self.unit_code = unit_code

    def to_etree(self):
        node = self._etree_node()
        node.text = str(self.amount)
        node.attrib["unitCode"] = self.unit_code
        return node

    def __str__(self):
        return "{} {}".format(self.amount, self.unit_code)

    def from_etree(self, root):
        self.amount = Decimal(root.text)
        self.unit_code = root.attrib['unitCode']
        return self


class CurrencyElement(StringElement):
    def __init__(self, namespace, tag, amount="", currency="EUR"):
        super().__init__(namespace, tag)
        self.amount = amount
        self.currency = currency

    def to_etree(self):
        node = self._etree_node()
        node.text = str(self.amount)
        node.attrib["currencyID"] = self.currency
        return node

    def from_etree(self, root):
        self.amount = Decimal(root.text)
        self.currency = root.attrib['currencyID']
        return self

    def __str__(self):
        return "{} {}".format(self.amount, self.currency)


class ClassificationElement(StringElement):
    def __init__(self, namespace, tag, text="", list_id="", list_version_id=""):
        super().__init__(namespace, tag)
        self.text = text
        self.list_id = list_id
        self.list_version_id = list_version_id

    def to_etree(self):
        node = self._etree_node()
        node.text = self.text
        node.attrib['listID'] = self.list_id
        node.attrib['listVersionID'] = self.list_version_id
        return node

    def from_etree(self, root):
        self.text = Decimal(root.text)
        self.list_id = root.attrib['listID']
        self.list_version_id = root.attrib['listVersionID']
        return self

    def __str__(self):
        return "{} ({} {})".format(self.text, self.list_id, self.list_version_id)


class AgencyIDElement(StringElement):
    def __init__(self, namespace, tag, text="", scheme_id=""):
        super().__init__(namespace, tag)
        self.text = text
        self.scheme_id = scheme_id

    def to_etree(self):
        node = self._etree_node()
        node.text = self.text
        node.attrib['schemeAgencyID'] = self.scheme_id
        return node

    def from_etree(self, root):
        self.text = Decimal(root.text)
        self.scheme_id = root.attrib['schemeAgencyID']
        return self

    def __str__(self):
        return "{} ({})".format(self.text, self.scheme_id)


class IDElement(StringElement):
    def __init__(self, namespace, tag, text="", scheme_id=""):
        super().__init__(namespace, tag)
        self.text = text
        self.scheme_id = scheme_id

    def to_etree(self):
        node = self._etree_node()
        node.text = self.text
        node.attrib['schemeID'] = self.scheme_id
        return node

    def from_etree(self, root):
        self.text = root.text
        self.scheme_id = root.attrib['schemeID']
        return self

    def __str__(self):
        return "{} ({})".format(self.text, self.scheme_id)


class DateTimeElement(StringElement):
    def __init__(self, namespace, tag, value=None, format='102'):
        super().__init__(namespace, tag)
        self.value = value
        self.format = format

    def to_etree(self):
        t = self._etree_node()
        node = ET.Element("{%s}%s" % (NS_UDT, "DateTimeString"))
        node.text = self.value.strftime("%Y%m%d")
        node.attrib['format'] = self.format
        t.append(node)
        return t

    def from_etree(self, root):
        if len(root) != 1:
            raise TypeError("Date containers should have one child")
        if root[0].tag != "{%s}%s" % (NS_UDT, "DateTimeString"):
            raise TypeError("Tag %s not recognized" % root[0].tag)
        if root[0].attrib['format'] != '102':
            raise TypeError("Date format %s cannot be parsed" % root[0].attrib['format'])
        self.value = datetime.strptime(root[0].text, '%Y%m%d').date()
        self.format = root[0].attrib['format']
        return self

    def __str__(self):
        return "{}".format(self.value)


class IndicatorElement(StringElement):
    def __init__(self, namespace, tag, value=None):
        super().__init__(namespace, tag)
        self.value = value

    def get_tag(self):
        return "{%s}%s" % (self.namespace, self.tag)

    def to_etree(self):
        t = self._etree_node()
        node = ET.Element("{%s}%s" % (NS_UDT, "Indicator"))
        node.text = self.value
        t.append(node)

    def __str__(self):
        return "{}".format(self.value)
