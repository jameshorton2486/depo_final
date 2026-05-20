from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default
    Extension="rels"
    ContentType="application/vnd.openxmlformats-package.relationships+xml"
  />
  <Default Extension="xml" ContentType="application/xml"/>
  <Override
    PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
  />
  <Override
    PartName="/word/styles.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"
  />
</Types>
"""

ROOT_RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship
    Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"
  />
</Relationships>
"""

DOCUMENT_RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
"""

STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
  </w:style>
</w:styles>
"""


def write_docx_export(rendered_document: dict[str, object], output_path: Path) -> Path:
    paragraphs_xml = [
        _paragraph_xml(line, 0, 0, center=True) for line in rendered_document["certificate_lines"]
    ]
    paragraphs_xml.append(_paragraph_xml("", 0, 0))
    for paragraph in rendered_document["paragraphs"]:
        paragraphs_xml.append(
            _paragraph_xml(
                "\t".join(part for part in paragraph["runs"] if part),
                int(paragraph["left_twips"]),
                int(paragraph["hanging_twips"]),
            )
        )
    if rendered_document["exhibit_index"]:
        paragraphs_xml.append(_paragraph_xml("", 0, 0))
        paragraphs_xml.append(_paragraph_xml("EXHIBIT INDEX", 0, 0, center=True))
        for entry in rendered_document["exhibit_index"]:
            paragraphs_xml.append(
                _paragraph_xml(f"{entry['label']}\t{entry['description']}", 360, 360)
            )

    document_xml = (
        """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>"""
        """<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">"""
        f"<w:body>{''.join(paragraphs_xml)}<w:sectPr/></w:body></w:document>"
    )

    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        archive.writestr("_rels/.rels", ROOT_RELS_XML)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/styles.xml", STYLES_XML)
        archive.writestr("word/_rels/document.xml.rels", DOCUMENT_RELS_XML)
    return output_path


def _paragraph_xml(text: str, left_twips: int, hanging_twips: int, *, center: bool = False) -> str:
    escaped = escape(text).replace("\t", '</w:t><w:tab/><w:t xml:space="preserve">')
    justification = '<w:jc w:val="center"/>' if center else ""
    indent = (
        f'<w:ind w:left="{left_twips}" w:hanging="{hanging_twips}"/>'
        if left_twips or hanging_twips
        else ""
    )
    tabs = f'<w:tabs><w:tab w:val="left" w:pos="{left_twips}"/></w:tabs>' if left_twips else ""
    return (
        "<w:p><w:pPr>"
        f"{justification}{tabs}{indent}"
        '</w:pPr><w:r><w:t xml:space="preserve">'
        f"{escaped}"
        "</w:t></w:r></w:p>"
    )
