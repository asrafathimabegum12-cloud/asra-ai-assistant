from pathlib import Path

from docx import Document

from backend.main import _generate_resume_docx_from_text


def test_generate_resume_docx_from_text_roundtrip(tmp_path: Path):
    source_text = "Summary\n\nEducation\nBS in Computer Science\n\nSkills\nPython, SQL\n\nExperience\nSoftware Engineer"
    output_path = tmp_path / "edited_resume.docx"

    _generate_resume_docx_from_text(source_text, output_path)

    assert output_path.exists()
    doc = Document(output_path)
    rendered_text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
    assert "Summary" in rendered_text
    assert "Python, SQL" in rendered_text
    assert "Software Engineer" in rendered_text
