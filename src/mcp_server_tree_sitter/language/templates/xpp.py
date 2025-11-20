"""Query templates for X++."""

TEMPLATES = {
    "classes": """
        (class_declaration
            name: (identifier) @class.name) @class.def
    """,
    "methods": """
        (method_declaration
            name: (identifier) @method.name) @method.def
    """,
    "fields": """
        (field_declaration
            name: (identifier) @field.name) @field.def
    """,
    "interfaces": """
        (interface_declaration
            name: (identifier) @interface.name) @interface.def
    """,
    "variables": """
        (variable_declaration
            name: (identifier) @variable.name) @variable.def
    """,
}
