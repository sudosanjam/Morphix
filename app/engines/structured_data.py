"""Structured data conversion: JSON, YAML, XML, and CSV."""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
import xml.etree.ElementTree as ET
import defusedxml.ElementTree as DefusedET

from app.engines.base import EngineCapability
from app.core.errors import ConversionFailedError


class StructuredDataEngine(EngineCapability):
    name = "structured_data"
    display_name = "Structured Data Engine"

    SUPPORTED_INPUTS = ["json", "yaml", "yml", "xml"]
    SUPPORTED_OUTPUTS = ["json", "yaml", "xml"]

    @classmethod
    def is_available(cls) -> bool:
        return True

    @classmethod
    def get_version(cls) -> Optional[str]:
        return f"pyyaml {yaml.__version__}"

    @classmethod
    def get_binary_path(cls) -> Optional[str]:
        return "bundled-python (json & yaml & xml)"

    @classmethod
    def _xml_to_dict(cls, element) -> Any:
        children = list(element)
        if not children:
            return element.text or ""
        result: Dict[str, Any] = {}
        for child in children:
            child_data = cls._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        return result

    @classmethod
    def _dict_to_xml(cls, tag: str, d: Any) -> ET.Element:
        elem = ET.Element(tag)
        if isinstance(d, dict):
            for key, val in d.items():
                # ensure valid tag name
                clean_tag = str(key).replace(" ", "_")
                if isinstance(val, list):
                    for item in val:
                        elem.append(cls._dict_to_xml(clean_tag, item))
                else:
                    elem.append(cls._dict_to_xml(clean_tag, val))
        elif isinstance(d, list):
            for item in d:
                elem.append(cls._dict_to_xml("item", item))
        else:
            elem.text = str(d) if d is not None else ""
        return elem

    @classmethod
    def convert(
        cls,
        source_path: Path,
        target_path: Path,
        target_format: str,
        settings: Dict[str, Any],
        progress_cb=None
    ) -> Path:
        """Convert data between JSON, YAML, and XML."""
        src_ext = source_path.suffix.lower().lstrip(".")
        if src_ext == "yml":
            src_ext = "yaml"

        tgt_fmt = target_format.lower()
        if tgt_fmt == "yml":
            tgt_fmt = "yaml"

        target_path.parent.mkdir(parents=True, exist_ok=True)
        indent = int(settings.get("indent", 2))
        sort_keys = bool(settings.get("sort_keys", False))

        if progress_cb:
            progress_cb(10, f"Parsing {src_ext.upper()} input...")

        try:
            # Parse source into Python dict/list
            parsed_data: Any = None
            if src_ext == "json":
                with open(source_path, "r", encoding="utf-8") as f:
                    parsed_data = json.load(f)
            elif src_ext == "yaml":
                with open(source_path, "r", encoding="utf-8") as f:
                    parsed_data = yaml.safe_load(f)
            elif src_ext == "xml":
                tree = DefusedET.parse(str(source_path))
                root = tree.getroot()
                parsed_data = {root.tag: cls._xml_to_dict(root)}
            else:
                raise ConversionFailedError(f"Unsupported source data format: {src_ext}")

            if progress_cb:
                progress_cb(60, f"Serializing to {tgt_fmt.upper()}...")

            # Output target
            if tgt_fmt == "json":
                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump(parsed_data, f, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
            elif tgt_fmt == "yaml":
                with open(target_path, "w", encoding="utf-8") as f:
                    yaml.dump(parsed_data, f, indent=indent, sort_keys=sort_keys, allow_unicode=True)
            elif tgt_fmt == "xml":
                root_tag = settings.get("root_tag", "root")
                root_elem = cls._dict_to_xml(root_tag, parsed_data)
                tree = ET.ElementTree(root_elem)
                ET.indent(tree, space="  " if indent > 0 else "")
                tree.write(str(target_path), encoding="utf-8", xml_declaration=True)
            else:
                raise ConversionFailedError(f"Unsupported target data format: {tgt_fmt}")

            if progress_cb:
                progress_cb(100, "Structured data serialized.")
            return target_path

        except Exception as e:
            if isinstance(e, ConversionFailedError):
                raise
            raise ConversionFailedError(f"Data conversion failed: {str(e)}")
