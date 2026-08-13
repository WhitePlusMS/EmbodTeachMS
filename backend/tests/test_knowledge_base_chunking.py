"""高级分段单一分隔符的领域测试。"""

from app.document_parsing.models import NormalizedDocument, ParsedBlock, SourceLocation
from app.knowledge_bases.chunking import ChunkingConfig, chunk_document


def normalized_document(*blocks: ParsedBlock) -> NormalizedDocument:
    return NormalizedDocument(
        markdown="\n\n".join(block.content for block in blocks),
        blocks=blocks,
        parser_name="test",
        parser_version="test-v1",
        content_sha256="test-hash",
    )


def test_advanced_punctuation_separator_splits_every_selected_boundary() -> None:
    document = normalized_document(
        ParsedBlock(
            block_id="paragraph-1",
            order=0,
            block_type="paragraph",
            content="第一句；第二句；第三句。",
            source=SourceLocation(line_start=1, line_end=1),
        )
    )

    chunks = chunk_document(
        document,
        knowledge_base_id="kb-1",
        document_id="doc-1",
        document_version=1,
        config=ChunkingConfig(mode="advanced", separators=("；",), overlap_characters=0),
    )

    assert [chunk.content for chunk in chunks] == ["第一句；", "第二句；", "第三句。"]


def test_advanced_heading_separator_splits_at_the_selected_heading_level() -> None:
    document = normalized_document(
        ParsedBlock(
            block_id="heading-1",
            order=0,
            block_type="heading",
            content="第一章",
            title_path=("第一章",),
            heading_level=1,
        ),
        ParsedBlock(
            block_id="paragraph-1",
            order=1,
            block_type="paragraph",
            content="第一章正文",
            title_path=("第一章",),
            heading_level=None,
        ),
        ParsedBlock(
            block_id="heading-2",
            order=2,
            block_type="heading",
            content="第二章",
            title_path=("第二章",),
            heading_level=1,
        ),
        ParsedBlock(
            block_id="paragraph-2",
            order=3,
            block_type="paragraph",
            content="第二章正文",
            title_path=("第二章",),
        ),
    )

    chunks = chunk_document(
        document,
        knowledge_base_id="kb-1",
        document_id="doc-1",
        document_version=1,
        config=ChunkingConfig(mode="advanced", separators=("#",), overlap_characters=0),
    )

    assert [chunk.content for chunk in chunks] == ["第一章\n\n第一章正文", "第二章\n\n第二章正文"]
