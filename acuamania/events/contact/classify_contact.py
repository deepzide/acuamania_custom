from acuamania.events.utils import (
        classify_resident,
        classify_group,
    )


def classify_contact(doc):
    """
    Classify the contact based on its attributes.
    """
    classify_resident(doc)
    classify_group(doc)