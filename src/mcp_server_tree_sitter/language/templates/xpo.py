"""Query templates for XPO."""

TEMPLATES = {
    "element_blocks": """
        (element_block) @element.def
    """,
    "element_types": """
        (element_type) @element_type.def
    """,
    "properties": """
        (properties_block) @properties.def
    """,
    "source_blocks": """
        (source_block) @source.def
    """,
    "fields": """
        (fields_block
            (property key: (identifier_word) @field.name) @field.def)
    """,
    "methods": """
        (methods_block
            (source_block (identifier) @method.name) @method.def)
    """,
    "identifiers": """
        (identifier) @identifier.name
    """,
    "guids": """
        (guid) @guid.value
    """,
}
