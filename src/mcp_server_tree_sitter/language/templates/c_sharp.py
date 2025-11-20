"""Query templates for C#."""

TEMPLATES = {
    "classes": """
        (class_declaration
            name: (identifier) @class.name) @class.def
    """,
    "methods": """
        (method_declaration
            name: (identifier) @method.name) @method.def
    """,
    "properties": """
        (property_declaration
            name: (identifier) @property.name) @property.def
    """,
    "interfaces": """
        (interface_declaration
            name: (identifier) @interface.name) @interface.def
    """,
    "using": """
        (using_directive) @using
    """,
}
